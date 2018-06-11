# -*- coding: utf-8 -*
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout
from django import forms
from django.db.models import Q

from express.utils import toTZDatetime
from pallets.models import Channel
from waybills.models import WaybillStatusEntry

PALLET_STATUS_CHOICES = (
    (0, "状态"),
    (1, "已生成"),
    (2, "已建提单"),
    (3, "已出库"),
)

AIRWAYBILL_STATUS_CHOICES = (
    (0, "状态"),
    (1, "已生成"),
    (2, "已出库"),
    (3, "国内派送"),
)


class PalletActionForm(forms.Form):
    actions = forms.ChoiceField(choices=(('', '---------'), ('1', u'生成提单')), required=False)

    def __init__(self, *args, **kwargs):
        super(PalletActionForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap3/layout/inline_field.html"
        self.helper.layout = Layout(
            'actions',
            Submit('exc', u'执行'),
        )


class PalletSearchForm(forms.Form):
    search = forms.CharField(label=u'托盘号或提单号', max_length=30, required=False)
    status = forms.ChoiceField(choices=PALLET_STATUS_CHOICES, label=u'状态', required=False)
    channel = forms.ModelChoiceField(Channel.objects.all().order_by('-id'), empty_label=u'渠道', to_field_name='name',
                                     required=False)
    creator = forms.CharField(label=u'创建人', max_length=30, required=False)
    remark = forms.CharField(label=u'备注', max_length=30, required=False)
    dt_start = forms.CharField(label=u'创建起始日期', required=False,
                               widget=forms.TextInput(attrs={'class': 'datepicker'}))

    dt_end = forms.CharField(label=u'创建截止日期', required=False,
                             widget=forms.TextInput(attrs={'class': 'datepicker'}))

    def __init__(self, *args, **kwargs):
        super(PalletSearchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap3/layout/inline_field.html"
        self.helper.form_method = "get"
        self.helper.form_action = "manage-pallets"
        self.helper.layout = Layout(
            'search',
            'status',
            'channel',
            'creator',
            'remark',
            'dt_start',
            'dt_end',
            Submit('', u'筛选'),
        )

    def addQuery(self, qs):
        if self.is_valid():
            search = self.cleaned_data["search"]
            status = self.cleaned_data["status"]
            creator = self.cleaned_data["creator"]
            remark = self.cleaned_data["remark"]
            dt_start = self.cleaned_data["dt_start"]
            dt_end = self.cleaned_data["dt_end"]
            channel = self.cleaned_data["channel"]

            q = Q()
            if search:
                q.add((Q(pallet_no__istartswith=search) | Q(air_waybill__air_waybill_no__istartswith=search)), Q.AND)

            if status:
                try:
                    status_id = int(status)
                    if status_id > 0:
                        if status_id == 1:  # 已生成
                            q.add(Q(air_waybill__isnull=True), Q.AND)
                        elif status_id == 2:  # 已建提单
                            q.add(Q(air_waybill__isnull=False), Q.AND)
                            q.add(Q(air_waybill__status=1), Q.AND)
                        elif status_id == 3:  # 已出库
                            q.add(Q(air_waybill__isnull=False), Q.AND)
                            q.add(Q(air_waybill__status__gte=2), Q.AND)
                except Exception as e:
                    pass
            if channel:
                q.add(Q(channel=channel), Q.AND)

            if creator:
                q.add(Q(user__username__iexact=creator), Q.AND)

            if remark:
                q.add(Q(remark__icontains=remark), Q.AND)

            if dt_start:
                q.add(Q(create_dt__gte=toTZDatetime(dt_start)), Q.AND)

            if dt_end:
                q.add(Q(create_dt__lt=toTZDatetime(dt_end)), Q.AND)

            return qs.filter(q)


class AirWaybillActionForm(forms.Form):
    actions = forms.ChoiceField(choices=(('', '---------'), ('1', u'导出运费')), required=False)

    def __init__(self, *args, **kwargs):
        super(AirWaybillActionForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap3/layout/inline_field.html"
        self.helper.layout = Layout(
            'actions',
            Submit('exc', u'执行'),
        )


class AirWaybillSearchForm(forms.Form):
    dt_start = forms.CharField(label=u'创建起始日期', required=False, widget=forms.TextInput(attrs={'class': 'datepicker'}))
    dt_end = forms.CharField(label=u'创建截止日期', required=False, widget=forms.TextInput(attrs={'class': 'datepicker'}))
    search = forms.CharField(label=u'托盘号或提单号', max_length=30, required=False)
    status = forms.ChoiceField(choices=AIRWAYBILL_STATUS_CHOICES, label=u'状态', required=False)
    channel = forms.ModelChoiceField(Channel.objects.all(), empty_label=u'渠道', required=False)

    def __init__(self, *args, **kwargs):
        super(AirWaybillSearchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap3/layout/inline_field.html"
        self.helper.form_method = "get"
        self.helper.form_action = "manage-air-waybill-list"
        self.helper.layout = Layout(
            'dt_start',
            'dt_end',
            'search',
            'status',
            'channel',
            Submit('', u'筛选'),
        )

    def addQuery(self, qs):
        if self.is_valid():
            dt_start = self.cleaned_data["dt_start"]
            dt_end = self.cleaned_data["dt_end"]
            search = self.cleaned_data["search"]
            status = self.cleaned_data["status"]
            channel = self.cleaned_data["channel"]

            q = Q()
            if search:
                q.add(Q(air_waybill_no__istartswith=search), Q.AND)
            if status:
                status_id = int(status)
                if status_id > 0:
                    q.add(Q(status=status_id), Q.AND)
            if channel:
                q.add(Q(channel=channel), Q.AND)
            if dt_start:
                q.add(Q(create_dt__gte=toTZDatetime(dt_start)), Q.AND)
            if dt_end:
                q.add(Q(create_dt__lte=toTZDatetime(dt_end)), Q.AND)
            return qs.filter(q)
