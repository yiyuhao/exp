# -*- coding: utf-8 -*
from django import forms
from django.forms import ModelForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout
from django.db.models import Q
from .models import *


class OrderForm(ModelForm):
    class Meta:
        model = Order
        fields = '__all__'
