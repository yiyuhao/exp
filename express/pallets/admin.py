from django.contrib import admin

# Register your models here.
from .models import *

from waybills.models import *


class AirlineAdmin(admin.ModelAdmin):
    class Meta:
        model = Airline


class ReceiverAdmin(admin.ModelAdmin):
    class Meta:
        model = Receiver


class CarrierAdmin(admin.ModelAdmin):
    class Meta:
        model = Carrier


class WaybillInline(admin.TabularInline):
    model = Waybill
    extra = 1
    fields = ['tracking_no', 'cn_tracking', 'weight']
    readonly_fields = ['tracking_no']


class PalletInLine(admin.TabularInline):
    model = Pallet
    extra = 1
    exclude = ['user']
    readonly_fields = ['pallet_no', 'weight']


class AirWaybillAdmin(admin.ModelAdmin):
    class Meta:
        model = AirWaybill

    inlines = [PalletInLine]
    list_display = ['air_waybill_no', 'get_waybills_count', 'last_modified', 'get_status']
    list_filter = ['last_modified']


class PalletAdmin(admin.ModelAdmin):
    class Meta:
        model = Pallet

    list_display = ['pallet_no', 'weight', 'air_waybill', 'create_dt', 'get_waybills_count', 'get_status']
    search_fields = ['pallet_no', 'air_waybill__air_waybill_no']
    list_filter = ['air_waybill__air_waybill_no', 'create_dt']


class ChannelAdmin(admin.ModelAdmin):
    class Meta:
        model = Channel

    list_display = ['id', 'name', 'loc', 'base_rate', 'next_rate', 'tax']
    search_fields = ['name', 'loc']


admin.site.register(Airline, AirlineAdmin)
admin.site.register(Receiver, ReceiverAdmin)
admin.site.register(Carrier, CarrierAdmin)
admin.site.register(AirWaybill, AirWaybillAdmin)
admin.site.register(Pallet, PalletAdmin)
admin.site.register(Channel, ChannelAdmin)
