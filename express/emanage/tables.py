# -*- coding: utf-8 -*
from __future__ import unicode_literals
import itertools
from decimal import ROUND_UP, Decimal

import django_tables2 as tables
from django.urls import reverse
from django.utils.safestring import mark_safe
from django_tables2.utils import A, AttributeDict  # alias for Accessor
from waybills.models import Waybill, ExceptionRecord
from waybills.models import WaybillStatus
from django.utils import timezone
from django.utils.html import format_html


class WaybillTable(tables.Table):
    class Meta:
        model = Waybill
        fields = ['counter', 'tracking_no', 'cn_tracking', 'status', 'src_loc', 'channel', 'person_id', 'fee',
                  'recv_name', 'recv_mobile',
                  'weight', 'pallet', 'create_dt', 'in_no', 'get_air_waybill']
        attrs = {'class': 'table table-responsive table-bordered table-striped table-hover'}  # add class to <table> tag

    counter = tables.Column(empty_values=(), orderable=False, verbose_name="#")

    tracking_no = tables.Column(verbose_name="国际运单号")
    cn_tracking = tables.Column(verbose_name="国内运单号")
    status = tables.Column(verbose_name="状态")
    src_loc = tables.Column(verbose_name="地点")
    weight = tables.Column(verbose_name="重量")
    create_dt = tables.Column(verbose_name="生成日期")
    recv_name = tables.Column(verbose_name="收件人")
    recv_mobile = tables.Column(verbose_name="收件人手机")

    edit = tables.LinkColumn(text='修改', orderable=False, verbose_name="修改")

    printBtn = tables.LinkColumn("customer_waybill_label", args=[A('pk')], text='打印', orderable=False,
                                 verbose_name="打印", attrs={'a': {'target': '_blank'}})
    in_no = tables.Column(verbose_name='建单批次')
    get_air_waybill = tables.Column(verbose_name='提单号', orderable=False)
    person_id = tables.Column(verbose_name='ID', empty_values=())

    fee = tables.Column(verbose_name='运费', orderable=False, empty_values=())

    def render_tracking_no(selfs, value, bound_column, record):
        return format_html(
            "<a target='_blank' href='/waybills/search/?tracking_no={tracking_no}&pre=manage'>{tracking_no}</a><br/> \
            <a class='fa fa-archive goods-detail' aria-hidden='true' data-toggle='{url}'></a> <small>个数: {qty}</small><br/> \
            <a class='fa fa-list-ul' aria-hidden='true'></a> <small>货架: {shelf_no}</small>"
            , tracking_no=value
            , url=reverse('manage-goods_detail-ajax', kwargs={"waybill_id": record.id})
            , qty=record.get_goods_quantity()
            , shelf_no=record.shelf_no
        )

    def render_counter(self):
        self.row_counter = getattr(self, 'row_counter', itertools.count(start=1))
        return mark_safe('<input type="checkbox" /> %d' % (next(self.row_counter)))

    def render_status(self, value, bound_column, record):
        statusEntry = value
        status = record.status_set.filter(status=statusEntry).first()

        return mark_safe(
            u' <p class="status" href="#" data-content="操作员: {user}" \
             rel="popover" data-placement="bottom" data-original-title="{create_dt}" data-trigger="hover">{status} {remark}</p>'.format(
                status=statusEntry, create_dt=timezone.localtime(status.create_dt).strftime('%y-%m-%d %H:%M:%S'),
                user=status.user.username if status.user else '',
                remark=',' + status.remark if status.remark else ''
            ))

    def render_edit(self, value, bound_column, record):
        return format_html("<a target='_blank' href='/admin/waybills/waybill/{id}/change/'>修改</a>", id=record.id)

    def render_person_id(selfs, value, bound_column, record):
        if not value:
            return u'无'
        else:
            return u'有'

    def render_fee(selfself, value, bound_column, record):
        return "${}".format(record.get_fee().quantize(Decimal('.01'), rounding=ROUND_UP))


class BulkPrintTable(tables.Table):
    class Meta:
        model = Waybill
        fields = ['cb', 'tracking_no', 'person_id', 'status', 'src_loc', 'shelf_no', 'channel', 'goods']
        attrs = {'class': 'table table-responsive table-bordered table-striped table-hover'}  # add class to <table> tag

    cb = tables.CheckBoxColumn(empty_values=(), orderable=False, verbose_name="#",
                               attrs={'input': {"type": 'checkbox'}},
                               accessor='pk')

    tracking_no = tables.Column(verbose_name="单号")
    shelf_no = tables.Column(verbose_name="货架号")
    status = tables.Column(verbose_name="状态")
    src_loc = tables.Column(verbose_name="地点")
    goods = tables.Column(verbose_name="商品", orderable=False)
    person_id = tables.Column(verbose_name='ID', empty_values=())

    # printBtn = tables.LinkColumn("customer_waybill_label", args=[A('pk')], text='仅打印', orderable=False,
    #                              verbose_name="打印", attrs={'a': {'target': '_blank'}})

    def render_goods(self, value, bound_column, record):
        return format_html(
            "<table class='table table-responsive table-bordered'>" + self.get_goods_tr(record) + "</table>")

    def get_goods_tr(self, record):
        result = """
         <tr>
            <th>架</th>
            <th>图</th>
            <th>码</th>
            <th>数</th>
            <th>描述</th>
            </tr>
        """

        for good in record.goods.all().order_by('id'):
            result += """
            <tr>
            <td>{5}</td>
            <td><img class='img' style='max-width: 200px; max-height: 200px' src={4}></img></td>
            <td>{0}</td>
            <td>{1}</td>
            <td>{2}<br/>{3}</td>
            </tr>""".format(good.sku, good.quantity, good.brand, good.description, good.img_url, good.shelf_no)

        return result

    def render_tracking_no(self, value, bound_column, record):
        return format_html(
            "{tracking_no}<br/>{cn_tracking}<br /> 个数: {qty}<br /> 批次: {in_no}"
            , tracking_no=value
            , cn_tracking='' if not record.cn_tracking else record.cn_tracking
            , qty=record.get_goods_quantity()
            , in_no=record.in_no
        )

    def render_cb(self, value, bound_column):
        self.row_counter = getattr(self, 'row_counter', itertools.count(start=1))
        default = {
            'type': 'checkbox',
            'name': bound_column.name,
            'value': value
        }

        general = self.attrs.get('input')
        specific = self.attrs.get('td__input')
        attrs = AttributeDict(default, **(specific or general or {}))
        return mark_safe('<input %s/> %d' % (attrs.as_html(), next(self.row_counter)))
        # return mark_safe('<input type="checkbox" /> %d' % (next(self.row_counter)))

    def render_status(self, value, bound_column, record):
        statusEntry = value
        status = record.status_set.filter(status=statusEntry).first()

        return mark_safe(
            u' <p class="status" href="#" data-content="操作员: {user}" \
             rel="popover" data-placement="bottom" data-original-title="{create_dt}" data-trigger="hover">{status}</p>'.format(
                status=statusEntry, create_dt=timezone.localtime(status.create_dt).strftime('%y-%m-%d %H:%M:%S'),
                user=status.user.username if status.user else ''))

    def render_person_id(selfs, value, bound_column, record):
        if not value:
            return u'无'
        else:
            return u'有'


class ExceptionRecordTable(tables.Table):
    class Meta:
        model = ExceptionRecord
        fields = ['cb', 'type', 'waybill', 'user', 'create_dt', 'remark', 'area', 'value', 'qty', 'description']
        attrs = {'class': 'table table-responsive table-bordered table-striped table-hover'}  # add class to <table> tag

    cb = tables.CheckBoxColumn(empty_values=(), orderable=False, verbose_name="#",
                               attrs={'input': {"type": 'checkbox'}},
                               accessor='pk')
    waybill = tables.Column(verbose_name="运单")
    type = tables.Column(verbose_name="类型")
    user = tables.Column(verbose_name="提交人")
    create_dt = tables.Column(verbose_name="提交时间")
    remark = tables.Column(verbose_name="备注", orderable=False)
    area = tables.Column(verbose_name='地区', empty_values=())
    value = tables.Column(verbose_name='价值', empty_values=())
    qty = tables.Column(verbose_name='个数', empty_values=())
    description = tables.Column(verbose_name='描述', empty_values=())
    images = tables.Column(verbose_name="内物图/破损图", orderable=False)

    def render_images(self, value, bound_column, record):
        return format_html(
            '<button class="btn btn-sm btn-default img" data={id}>图片</button>'
            '<a class="btn btn-sm btn-default img" style="margin-left:5px" href="/manage/exception-list/delete-record/{id}" target="_blank">删除记录</a>'
            , id=record.id
        )

    def render_waybill(selfself, value):
        return format_html(
            "<a href='/admin/waybills/waybill/{id}/change' target='_blank'>{tracking_no}</a>"
            , id=value.id
            , tracking_no=value.tracking_no
        )
