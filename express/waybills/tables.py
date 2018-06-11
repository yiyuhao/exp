# -*- coding: utf-8 -*
import itertools
from decimal import Decimal, ROUND_DOWN, ROUND_UP

import django_tables2 as tables
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django_tables2.utils import A, AttributeDict  # alias for Accessor
from .models import Waybill, WaybillStatusEntry
from waybills.models import WaybillStatus


class WaybillTable(tables.Table):
    class Meta:
        model = Waybill
        fields = ['cb', 'tracking_no', 'cn_tracking', 'status_order_index', 'recv_name', 'recv_mobile', 'weight', 'fee',
                  'create_dt', 'in_no', 'edit', 'delete']
        attrs = {'class': 'table table-responsive table-bordered table-striped table-hover'}  # add class to <table> tag

    cb = tables.CheckBoxColumn(verbose_name="#", attrs={'input': {"type": 'checkbox'}}, accessor='pk', orderable=False)

    edit = tables.LinkColumn("customer_waybill_detail", args=[A('pk')], empty_values=(), text='修改', orderable=False,
                             verbose_name="编辑")
    # tracking_no = tables.Column(verbose_name="国际运单号")
    tracking_no = tables.LinkColumn("customer_waybill_search", text=A('tracking_no'), verbose_name="国际运单号")

    cn_tracking = tables.Column(verbose_name="国内运单号")
    status_order_index = tables.Column(verbose_name="状态")
    weight = tables.Column(verbose_name="重量")
    create_dt = tables.Column(verbose_name="生成日期")
    recv_name = tables.Column(verbose_name="收件人")
    recv_mobile = tables.Column(verbose_name="收件人手机")
    delete = tables.LinkColumn("waybill-detail", args=[A('pk')], text='删除', orderable=False, verbose_name="删除")
    printBtn = tables.LinkColumn("customer_waybill_print", args=[A('pk')], text='打印', orderable=False,
                                 verbose_name="打印")
    in_no= tables.Column(verbose_name='建单批次')
    fee = tables.Column(verbose_name='运费', orderable=False, empty_values=())

    def render_tracking_no(self, value):
        attrs = 'href=/waybills/search/?tracking_no=%s target=_blank' % value

        return format_html(
            '<a {attrs}>{text}</a>',
            attrs=attrs,
            text=value
        )

    def render_status_order_index(self, value):
        if value is None:
            return ""
        else:
            return str(WaybillStatusEntry.objects.get(order_index=value))

    def render_cb(self, value, bound_column, record):
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

    def render_fee(selfself, value, bound_column, record):
        return "${}".format (record.get_fee().quantize(Decimal('.01'), rounding=ROUND_UP))