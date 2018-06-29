# -*- coding: utf-8 -*
import itertools

from django.urls import reverse
from django.utils.safestring import mark_safe
import django_tables2 as tables
from django_tables2.utils import AttributeDict, A

from .models import *
from waybills.models import *


class AirWaybillTable(tables.Table):
    class Meta:
        model = AirWaybill
        fields = ['cb', 'air_waybill_no', 'channel', 'get_pallets_count', 'get_waybills_count',
                  'get_finish_waybills_count', 'get_not_finish_waybills_count', 'create_dt', 'get_status', 'edit',
                  'action', 'get_weight']
        attrs = {'class': 'table table-responsive table-bordered table-striped table-hover'}  # add class to <table> tag

    cb = tables.CheckBoxColumn(verbose_name="#", attrs={'input': {"type": 'checkbox'}}, accessor='pk', orderable=False)

    # edit = tables.Column(accessor='pk', empty_values=(), orderable=False, verbose_name="导出")

    action = tables.Column(empty_values=(), orderable=False, verbose_name='操作')

    create_dt = tables.DateTimeColumn(verbose_name='创建时间')

    get_status = tables.Column(verbose_name="状态", order_by=('status'))

    get_waybills_count = tables.Column(verbose_name="包裹数", orderable=False)

    get_finish_waybills_count = tables.Column(verbose_name="已完成", orderable=False)

    get_not_finish_waybills_count = tables.Column(verbose_name="未完成", orderable=False)

    get_pallets_count = tables.Column(verbose_name="托盘数", orderable=False)

    get_weight = tables.Column(verbose_name="重量", orderable=False)

    edit = tables.TemplateColumn(
        u"""
              {% if perms.pallets.can_export_air_waybill %}
                <a class="btn btn-sm btn-default export" href="{% url "manage-agent-files" record.id %}" target="_blank">货代</a> 
                <a class="btn btn-sm btn-default export" href="{% url "manage-customs-files" record.id %}" target="_blank">电商</a> 
                <a class="btn btn-sm btn-default export" href="{% url "manage-usps-files" record.id %}" target="_blank">USPS</a> 
                <a class="btn btn-sm btn-default export" href="{% url "manage-both-tracking-files" record.id %}" target="_blank">双边单号</a>
                <a class="btn btn-sm btn-default export" href="{% url "manage-id-cards-files" record.id %}" target="_blank">身份证图片压缩包</a>
                {% endif %}
        """, empty_values=(), orderable=False, verbose_name="导出")

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

    def render_air_waybill_no(self, value, bound_column, record):
        return mark_safe(
            u'<a href="/admin/pallets/airwaybill/{id}/change/" target="_blank" >{value}</a>'.format(
                id=record.id, value=value))

    # def render_edit(self, value, bound_column, record):
    #     return mark_safe(u'<a class="btn btn-sm btn-default export" href="%s" target="_blank">货代</a> \
    #                        <a class="btn btn-sm btn-default export" href="%s" target="_blank">电商</a> \
    #                       <a class="btn btn-sm btn-default export" href="%s" target="_blank">USPS</a> \
    #                       <a class="btn btn-sm btn-default export" href="%s" target="_blank">双边单号</a>' % (
    #         reverse('manage-agent-files', kwargs={"pk": record.id}),
    #         reverse('manage-customs-files', kwargs={"pk": record.id}),
    #         reverse('manage-usps-files', kwargs={"pk": record.id}),
    #         reverse('manage-both-tracking-files', kwargs={"pk": record.id})))

    def render_action(self, value, bound_column, record):
        return mark_safe(
            u'''<a class="btn btn-sm btn-primary send-out" data-toggle="{id}">出库</a> 
                <a class="btn btn-sm btn-success airline-update" data-toggle="{id}">更新航班信息</a> 
                <a class="btn btn-sm btn-warning cn-deliver" data-toggle="{id}">国内派送</a> 
              '''
                .format(id=record.id))

    def render_get_status(self, value, bound_column, record):
        return mark_safe(
            u'{status} <br/> <small>{last_modified}</small>'.format(status=value,
                                                                    last_modified=record.last_modified.strftime(
                                                                        "%y-%m-%d")))

    def render_get_weight(self, value, bound_column, record):
        return mark_safe(
            u'<small>Lb:{status}</small>  <br/> <small>Kg:{kg}</small>'.format(status=value,
                                                                               kg=round(value * Decimal('0.453592'),
                                                                                        2)))


class PalletTable(tables.Table):
    class Meta:
        model = Pallet
        fields = ['cb', 'pallet_no', 'user', 'channel', 'remark', 'total_cnt', 'weight', 'air_waybill', 'status',
                  'create_dt']
        attrs = {'class': 'table table-responsive table-bordered table-striped table-hover'}  # add class to <table> tag

    cb = tables.CheckBoxColumn(verbose_name="#", attrs={'input': {"type": 'checkbox'}}, accessor='pk', orderable=False)

    pallet_no = tables.Column(verbose_name="托盘号")

    total_cnt = tables.Column(verbose_name='总包裹数', empty_values=(), orderable=False)

    weight = tables.Column(verbose_name='总重量')

    air_waybill = tables.Column(verbose_name="提单号")

    create_dt = tables.Column(verbose_name="创建日期")

    status = tables.Column(verbose_name="状态", empty_values=(), orderable=False)

    user = tables.Column(verbose_name="创建人")

    channel = tables.Column(verbose_name="渠道", empty_values=())

    remark = tables.Column(verbose_name="备注", empty_values=())

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
        return mark_safe('<input %s id=%d/> %d' % (attrs.as_html(), record.id, next(self.row_counter)))

    def render_total_cnt(self, value, bound_column, record):
        # todo how to sort
        cnt = Waybill.objects.filter(pallet=record).count()
        return cnt

    def render_status(self, value, bound_column, record):
        return record.get_status()

    def render_pallet_no(self, value, bound_column, record):
        return mark_safe(
            u'<a href="/admin/pallets/pallet/{id}/change/" target="_blank" >{value}</a>'.format(
                id=record.id, value=value))
