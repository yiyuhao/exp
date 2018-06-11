# -*- coding: utf-8 -*
from django.urls import reverse
from django.views.decorators.cache import never_cache

from .forms import UserLoginForm, UserRegisterForm, CustomerProfileForm, EmployeeProfileForm

from django.contrib.auth import (
    authenticate,
    login,
    logout,
)

from django.shortcuts import render, redirect

from models import Customer, Employee

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import views as auth_views


@login_required()
def customer_profile_view(request):
    customer = None
    if Customer.objects.filter(user=request.user).exists():
        customer = Customer.objects.get(user=request.user)

    if request.method == "POST":
        form = CustomerProfileForm(request.POST or None, instance=customer)

        if form.is_valid():
            if customer is None:
                customer = form.save(commit=False)
                customer.user = request.user
                customer.save()
            else:
                form.save()
            messages.success(request, '更新成功')

    else:
        if customer is None:
            messages.info(request, '请补全客户基本信息')
            form = CustomerProfileForm()
        else:
            form = CustomerProfileForm(request.POST or None, instance=customer)

    title = "Profile"

    return render(request, "accounts/profile.html",
                  {"form": form,
                   "title": title,
                   "submit_value": u'更新',
                   "base_template": "waybills/customer_base.html"
                   }
                  )


@login_required(login_url='/manage/login/')
def manage_profile_view(request):
    employee = None

    if Employee.objects.filter(user=request.user).exists():
        employee = Employee.objects.get(user=request.user)

    if request.method == "POST":
        form = EmployeeProfileForm(request.POST or None, instance=employee)

        if form.is_valid():
            if employee is None:
                employee = form.save(commit=False)
                employee.user = request.user
                employee.save()
            else:
                form.save()
            messages.success(request, '更新成功')

    else:
        if employee is None:
            messages.info(request, '请补全雇员基本信息')
            form = EmployeeProfileForm()
        else:
            form = EmployeeProfileForm(request.POST or None, instance=employee)

    title = "Profile"

    return render(request, "accounts/profile.html",
                  {"form": form,
                   "title": title,
                   "submit_value": u'更新',
                   "base_template": "manage/manage_base.html"
                   }
                  )


@never_cache
def customer_login_view(request):
    if request.method == "POST":
        set_user_timezone(request)

    return auth_views.login(request)


def set_user_timezone(request):
    ''' set user session timezone when login'''
    try:
        user_tz = request.POST.get('user_tz')
        if user_tz:
            request.session['django_timezone'] = user_tz
    except Exception as e:
        return
