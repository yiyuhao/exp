# -*- coding: utf-8 -*
from django import forms

from .models import *

from django.forms import inlineformset_factory, ModelForm

from django.db.models import Model

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout
from django.db.models import Q

class WaybillSearchForm(forms.Form):
    tracking_no = forms.CharField(label=u'国际运单号', max_length=100, required=False)
    recv_name = forms.CharField(label=u'收件人', max_length=100, required=False)
    status = forms.ModelChoiceField(WaybillStatusEntry.objects.all().order_by("order_index"),empty_label=u'状态', to_field_name="order_index", required=False)
    per_page = forms.IntegerField(label=u'每页显示个数', max_value=100, required=False)

    def __init__(self, *args, **kwargs):
        super(WaybillSearchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap3/layout/inline_field.html"
        self.helper.form_method = "get"
        self.helper.form_action = "customer_waybill_list"
        self.helper.layout = Layout(
            'tracking_no',
            'recv_name',
            'status',
            'per_page',
            Submit('', u'筛选'),
        )

    def addQuery(self, qs):
        if self.is_valid():
            tracking_no = self.cleaned_data["tracking_no"]
            recv_name = self.cleaned_data["recv_name"]
            status = self.cleaned_data["status"]

            q = Q()
            if tracking_no:
                q.add(Q(tracking_no__icontains=tracking_no), Q.AND)
            if recv_name:
                q.add(Q(recv_name__icontains=recv_name), Q.AND)
            if status:
                q.add(Q(status_order_index=status.order_index), Q.AND)
            return qs.filter(q)

class WaybillBatchActionForm(forms.Form):
    print_waybill = forms.ChoiceField(choices=(('','---------'),('1',u'批量打印')), required=False)

    def __init__(self, *args, **kwargs):
        super(WaybillBatchActionForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap3/layout/inline_field.html"
        self.helper.form_method = "post"
        self.helper.form_action = "customer_waybill_list"
        self.helper.layout = Layout(
            'print_waybill',
            Submit('', u'执行'),
        )


class WaybillForm(ModelForm):
    # 省市区
    recv_province = forms.CharField(widget=forms.HiddenInput, required=True)
    recv_city = forms.CharField(widget=forms.HiddenInput, required=True)
    recv_area = forms.CharField(widget=forms.HiddenInput, required=True)
    order_no = forms.CharField(label=u'自定义单号', required=False)
    remark = forms.CharField(label=u'备注', required=False)

    recv_name = forms.CharField(label=u'收件人姓名', required=True)
    recv_address = forms.CharField(label=u'收件人地址', required=True)
    recv_zipcode = forms.CharField(label=u'收件人邮编', required=True)
    recv_mobile = forms.CharField(label=u'收件人手机', required=True)
    recv_phone = forms.CharField(label=u'电话', required=False)

    send_name = forms.CharField(label=u'发件人姓名', required=True)
    send_mobile = forms.CharField(label=u'发件人电话', required=True)
    send_address = forms.CharField(label=u'发件人地址', required=True)

    weight = forms.DecimalField(widget=forms.HiddenInput(), required=False)
    tracking_no = forms.CharField(widget=forms.HiddenInput(attrs={"style": 'display:none;'}), required=False)

    class Meta:
        model = Waybill
        fields = ['recv_province', 'recv_city', 'recv_area', 'recv_address', 'recv_zipcode', 'recv_name', 'recv_mobile',
                  'recv_phone', 'order_no', 'remark', 'send_name', 'send_mobile', 'send_address', 'weight',
                  'tracking_no']

    def __init__(self, *args, **kwargs):
        super(WaybillForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-2'
        self.helper.field_class = 'col-md-8'
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'recv_province', 'recv_city', 'recv_area', 'recv_address', 'recv_zipcode', 'recv_name', 'recv_mobile',
            'recv_phone', 'order_no', 'remark', 'send_name', 'send_mobile', 'send_address',
        )


class UploadFileForm(forms.Form):
    file = forms.FileField(label="运单文件", widget=forms.FileInput(attrs={"accept": ".xls,.xlsx"}))

    def __init__(self, *args, **kwargs):
        super(UploadFileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'file',
            Submit('submit', u'导入'),
        )

class GoodForm(ModelForm):
    class Meta:
        model = Good
        fields = ['cat1', 'cat2', 'brand', 'description', 'quantity', 'unit_price','unit_weight', 'remark']