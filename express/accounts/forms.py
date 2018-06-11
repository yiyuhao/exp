# -*- coding: utf-8 -*
from django import forms
from django.forms import (
    Form,
    ModelForm,
    CharField,
    EmailField,
    TextInput,
    PasswordInput,
    ValidationError,
    ModelChoiceField,
)
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from waybills.models import Location
from .models import *


class UserLoginForm(Form):
    username = CharField(max_length=150)
    password = CharField(widget=PasswordInput)

    def clean(self):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']

        # auth
        user = authenticate(username=username, password=password)
        if user is None or not user.is_active:
            raise ValidationError('Fail to login, username or password not correct.')

        return self.cleaned_data


class UserRegisterForm(ModelForm):
    username = CharField(max_length=150)
    password = CharField(widget=PasswordInput)
    email = EmailField(required=True)

    class Meta:
        model = User
        fields = [
            'username',
            'password',
            'email',
            'first_name',
            'last_name',
        ]

    def clean(self):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        email = self.cleaned_data['email']
        user_count = User.objects.filter(username=username).count()
        if user_count > 0:
            raise ValidationError("%s is already existed" % username)
        email_count = User.objects.filter(email=email).count()
        if email_count > 0:
            raise ValidationError("%s is already existed" % email)
        return self.cleaned_data


class CustomerProfileForm(ModelForm):
    loc = forms.ModelChoiceField(Location.objects.filter(is_us_node=True))

    class Meta:
        model = Customer
        fields = [
            'mobile',
            'repr_name',
            'address',
            'loc',
        ]


class EmployeeProfileForm(ModelForm):
    loc = forms.ModelChoiceField(Location.objects.filter(is_us_node=True))

    class Meta:
        model = Employee
        fields = [
            "loc"
        ]
