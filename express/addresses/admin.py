from django.contrib import admin
from .models import *


class ExpressMarkAdmin(admin.ModelAdmin):
    class Meta:
        model = ExpressMark

    search_fields = ['province', 'city', 'area', 'ems_mark1']
    list_display = ['province', 'city', 'area', 'ems_mark1']


class PeopleAdmin(admin.ModelAdmin):
    class Meta:
        model = People

    search_fields = ['name', 'id_no', 'mobile']
    list_display = ['name', 'id_no', 'mobile', 'id_card_backside', 'id_card_front']


admin.site.register(People, PeopleAdmin)
admin.site.register(ExpressMark, ExpressMarkAdmin)
