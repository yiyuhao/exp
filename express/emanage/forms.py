# -*- coding: utf-8 -*
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout
from django import forms
from django.db.models import Q, Max, Sum
from django.utils import timezone

from express.utils import toTZDatetime
from pallets.models import Channel, CH_LIST_REQUIRED_PERSON_ID
from waybills.models import WaybillStatusEntry, SrcLoc, Waybill, ExceptionRecord

WAYBILL_ACTIONS = (
    (1, "--------"),
    (2, "更新USPS"),
    (3, "导出"),
    (4, "添加韵达单号"),
    (5, "导出虚拟单"),
    (6, "更新虚拟单"),
    (7, "导出八达通表格"),
    (8, "导出青岛电商"),
    (9, "更新国内单号"),
    (10, "更新包裹重量"),
    (11, "批量导出指定面单"),
    (12, "导出地址信息"),
    (13, "更换国内单号"),
    (14, "更换渠道"),
    (15, "自动获取单号"),
    (16, "EMS代码"),
    (17, "批量打sku面单"),
    (18, "导出清关数据"),
    (19, "更改人名"),
    (20, "运单时效"),
    (21, "延长收货表"),
    (22, "导出Q渠道"),
)

PERSON_ID_SELECT = (
    (0, '身份证'),
    (1, '无'),
    (2, '有'),
)

CN_TRACKING_SELECT = (
    (0, '国内单号'),
    (1, '无'),
    (2, '有')
)

EXCEPTION_RECORD_TYPE = (
    ('', '类型'),
    ('丢件', '丢件'),
    ('破损', '破损')
)

EXCEPTION_RECORD_AREA = (
    ('', '区域'),
    ('美国', '美国'),
    ('中国', '中国')
)


class ManageWaybillSearchForm(forms.Form):
    search = forms.CharField(label=u'搜索', max_length=30, required=False)
    in_no = forms.CharField(label=u'建单批次', max_length=30, required=False)
    status = forms.ModelChoiceField(WaybillStatusEntry.objects.all().order_by("order_index"), empty_label=u'状态',
                                    to_field_name="order_index", required=False)
    src_loc = forms.ModelChoiceField(SrcLoc.objects.all().order_by('id'), empty_label=u'地点', to_field_name='name',
                                     required=False)

    channel = forms.ModelChoiceField(Channel.objects.all().order_by('id'), empty_label=u'渠道', to_field_name='name',
                                     required=False)
    has_person_id = forms.ChoiceField(PERSON_ID_SELECT, label=u'身份证', required=False)

    has_cn_tracking = forms.ChoiceField(CN_TRACKING_SELECT, label=u'国内单号', required=False)

    dt_start = forms.CharField(label=u'起始日期', required=False,
                               widget=forms.TextInput(attrs={'class': 'datepicker'}))
    dt_end = forms.CharField(label=u'截止日期', required=False,
                             widget=forms.TextInput(attrs={'class': 'datepicker'}))
    multi_search = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 1, 'cols': 20}), label=u'多单号搜索', required=False)

    status_dt_start = forms.CharField(label=u'状态起始日期', required=False,
                                      widget=forms.TextInput(attrs={'class': 'datepicker'}))

    status_dt_end = forms.CharField(label=u'状态截止日期', required=False,
                                    widget=forms.TextInput(attrs={'class': 'datepicker'}))

    qty = forms.IntegerField(label='个数', min_value=1, required=False)

    def __init__(self, *args, **kwargs):
        super(ManageWaybillSearchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap3/layout/inline_field.html"
        self.helper.form_method = "get"
        self.helper.form_action = "manage-waybills"
        self.helper.layout = Layout(
            'search',
            'in_no',
            'status',
            'src_loc',
            'channel',
            'has_person_id',
            'has_cn_tracking',
            'dt_start',
            'dt_end',
            'multi_search',
            'status_dt_start',
            'status_dt_end',
            'qty',
            Submit('', u'筛选'),
        )

    def addQuery(self, loc):
        if self.is_valid():
            search = self.cleaned_data["search"]
            status = self.cleaned_data["status"]
            src_loc = self.cleaned_data["src_loc"]
            channel = self.cleaned_data["channel"]
            dt_start = self.cleaned_data["dt_start"]
            dt_end = self.cleaned_data["dt_end"]
            multi_search = self.cleaned_data["multi_search"]
            has_person_id = self.cleaned_data["has_person_id"]
            has_cn_tracking = self.cleaned_data["has_cn_tracking"]
            in_no = self.cleaned_data["in_no"]
            status_dt_start = self.cleaned_data["status_dt_start"]
            status_dt_end = self.cleaned_data["status_dt_end"]
            qty = self.cleaned_data["qty"]
            status_order_index = None
            if status:
                status_order_index = status.order_index

            return Waybill.query_filter(channel, dt_end, dt_start, has_cn_tracking, has_person_id, in_no, loc,
                                        multi_search, qty, search, src_loc, status_dt_end, status_dt_start,
                                        status_order_index)


class WaybillActionForm(forms.Form):
    action = forms.ChoiceField(choices=WAYBILL_ACTIONS, required=False)
    change_channel = forms.ModelChoiceField(Channel.objects.all().order_by('id'), empty_label=u'渠道',
                                            to_field_name='name',
                                            required=False)
    file = forms.FileField(allow_empty_file=False)

    def __init__(self, *args, **kwargs):
        super(WaybillActionForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap3/layout/inline_field.html"
        self.helper.form_method = "post"
        self.helper.form_action = ""
        self.helper.layout = Layout(
            'action',
            'change_channel',
            'file',
            Submit('action-submit', u'执行'),
        )


class BatchCheckForm(forms.Form):
    file = forms.FileField(allow_empty_file=False)

    def __init__(self, *args, **kwargs):
        super(BatchCheckForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap3/layout/inline_field.html"
        self.helper.form_method = "post"
        self.helper.form_action = ""
        self.helper.layout = Layout(
            'file',
            Submit('action-submit', u'上传'),
        )


class BulkPrintSearchForm(forms.Form):
    dt = forms.CharField(label=u'身份证上传日期', required=False,
                         widget=forms.TextInput(attrs={'class': 'datepicker'}))

    goods_no = forms.CharField(label=u'条码', max_length=40, required=False)

    in_no = forms.CharField(label=u'批次', max_length=30, required=False)

    shelf_no = forms.CharField(label=u'货架号', max_length=30, required=False)

    src_loc = forms.ModelChoiceField(SrcLoc.objects.all().order_by('id'), empty_label=u'地点', to_field_name='name',
                                     required=True)

    channel = forms.ModelChoiceField(Channel.objects.all().order_by('id'), empty_label=u'渠道', to_field_name='name',
                                     required=False)

    def __init__(self, *args, **kwargs):
        super(BulkPrintSearchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap3/layout/inline_field.html"
        self.helper.form_method = "get"
        self.helper.form_action = "manage-waybills-bulk-print"
        self.helper.layout = Layout(
            'dt',
            'goods_no',
            'in_no',
            'shelf_no',
            'src_loc',
            'channel',
            Submit('', u'筛选'),
        )

    def addQuery(self, qs):
        if self.is_valid():
            goods_no = self.cleaned_data["goods_no"]
            in_no = self.cleaned_data["in_no"]
            shelf_no = self.cleaned_data["shelf_no"]
            src_loc = self.cleaned_data["src_loc"]
            channel = self.cleaned_data["channel"]
            dt = self.cleaned_data['dt']

            q = Q()
            if dt and toTZDatetime(dt):
                q.add(Q(upload_person_id_dt__lt=toTZDatetime(dt) + timezone.timedelta(days=1)), Q.AND)

            if goods_no:
                q.add(Q(goods__sku__iexact=goods_no), Q.AND)

            if in_no:
                q.add(Q(in_no__istartswith=in_no), Q.AND)
            else:
                q.add(Q(in_no__istartswith='HH') | Q(in_no__istartswith='HC'), Q.AND)

            if src_loc:
                q.add(Q(src_loc=src_loc), Q.AND)

            if channel:
                q.add(Q(channel=channel), Q.AND)

            if shelf_no:
                q.add(Q(shelf_no__iexact=shelf_no), Q.AND)

            return qs.filter(q).distinct()


class BulkPrintMultiSearchForm(forms.Form):
    dt = forms.CharField(label=u'身份证上传日期', required=False,
                         widget=forms.TextInput(attrs={'class': 'datepicker'}))

    src_loc = forms.ModelChoiceField(SrcLoc.objects.all().order_by('id'), empty_label=u'地点', to_field_name='name',
                                     required=True)

    channel = forms.ModelChoiceField(Channel.objects.all().order_by('id'), empty_label=u'渠道', to_field_name='name',
                                     required=False)
    shelf_no = forms.CharField(label=u'货架号', max_length=30, required=False)

    def __init__(self, *args, **kwargs):
        super(BulkPrintMultiSearchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap3/layout/inline_field.html"
        self.helper.form_method = "get"
        self.helper.form_action = "manage-waybills-bulk-print-multi"
        self.helper.layout = Layout(
            'dt',
            'shelf_no',
            'src_loc',
            'channel',
            Submit('', u'筛选'),
        )

    def addQuery(self, qs):
        if self.is_valid():
            src_loc = self.cleaned_data["src_loc"]
            channel = self.cleaned_data["channel"]
            dt = self.cleaned_data['dt']
            shelf_no = self.cleaned_data["shelf_no"]

            q = Q()
            if dt and toTZDatetime(dt):
                q.add(Q(upload_person_id_dt__lt=toTZDatetime(dt) + timezone.timedelta(days=1)), Q.AND)

            if src_loc:
                q.add(Q(src_loc=src_loc), Q.AND)

            if channel:
                q.add(Q(channel=channel), Q.AND)

            if shelf_no:
                q.add(Q(shelf_no__icontains=shelf_no), Q.AND)

            q.add(Q(in_no__istartswith='HH') | Q(in_no__istartswith='HC'), Q.AND)

            return qs.filter(q).distinct()


class ExceptionRecordSearchForm(forms.Form):
    tracking_no = forms.CharField(label=u'搜索', max_length=30, required=False)
    type = forms.ChoiceField(EXCEPTION_RECORD_TYPE, label=u'类型', required=False)
    area = forms.ChoiceField(EXCEPTION_RECORD_AREA, label=u'区域', required=False)

    def __init__(self, *args, **kwargs):
        super(ExceptionRecordSearchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap3/layout/inline_field.html"
        self.helper.form_method = "get"
        self.helper.form_action = "manage-exception-list"
        self.helper.layout = Layout(
            'tracking_no',
            'type',
            'area',
            Submit('', u'筛选'),
        )

    def addQuery(self):
        if self.is_valid():
            tracking_no = self.cleaned_data["tracking_no"].strip()
            type = self.cleaned_data["type"].strip()
            area = self.cleaned_data["area"].strip()
            q = Q()
            if tracking_no:
                q.add((Q(waybill__tracking_no__iexact=tracking_no) | Q(waybill__cn_tracking__iexact=tracking_no)),
                      Q.AND)
            if type:
                q.add(Q(type__iexact=type), Q.AND)
            if area:
                q.add(Q(area__iexact=area), Q.AND)
            return ExceptionRecord.objects.filter(q)


class ManagePerformanceSearchForm(forms.Form):
    dt_st = forms.CharField(label=u'美国日期开始', max_length=30, required=True,
                            widget=forms.TextInput(attrs={'class': 'datepicker'}),
                            initial=(timezone.now() + timezone.timedelta(days=-7)).date().strftime('%m/%d/%Y'))
    dt_ed = forms.CharField(label=u'美国日期截止', max_length=30, required=True,
                            widget=forms.TextInput(attrs={'class': 'datepicker'}),
                            initial=timezone.now().date().strftime('%m/%d/%Y'))

    def __init__(self, *args, **kwargs):
        super(ManagePerformanceSearchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap3/layout/inline_field.html"
        self.helper.form_method = "get"
        self.helper.form_action = "manage-performance"
        self.helper.layout = Layout(
            'dt_st',
            'dt_ed',
            Submit('', u'查询'),
        )
