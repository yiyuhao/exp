from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from rest_framework.authtoken.admin import TokenAdmin


from .models import *


class CustomerInline(admin.StackedInline):
    model = Customer
    can_delete = False
    verbose_name_plural = 'Customer'


class EmployeeInline(admin.StackedInline):
    model = Employee
    can_delete = False
    verbose_name_plural = 'Employee'


class UserAdmin(BaseUserAdmin):
    inlines = (CustomerInline, EmployeeInline)


class CustomerAdmin(admin.ModelAdmin):
    class Meta:
        model = Customer

    list_display = ["user", 'repr_name', "mobile", "address"]
    list_display_links = ["user"]
    search_fields = ['repr_name', "mobile"]
    readonly_fields = ["user"]


class EmployeeAdmin(admin.ModelAdmin):
    class Meta:
        model = Employee

    list_display = ["user", 'loc']
    list_display_links = ["user"]
    search_fields = ['loc']
    readonly_fields = ["user"]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(Customer, CustomerAdmin)
TokenAdmin.raw_id_fields = ('user',)
