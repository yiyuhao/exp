from django.contrib import admin
from django.utils.html import format_html

from .models import *


class GoodInLine(admin.TabularInline):
    model = Good
    extra = 1
    # fields = ['cat1', 'cat2', 'brand', 'description', 'quantity',
    #           'weight', 'price']


class WaybillStatusInLine(admin.TabularInline):
    model = WaybillStatus
    extra = 1


class WaybillAdmin(admin.ModelAdmin):
    class Meta:
        model = Waybill

    #
    # fieldsets = [
    #     ('Waybill info', {'fields': ['tracking_no', 'remark']}),
    #     # ('Date info', {'fields': ['create_dt', 'last_modified'], 'classes': ['collapse']})
    # ]

    inlines = [GoodInLine, WaybillStatusInLine]

    readonly_fields = [
        "tracking_no",
        "cn_tracking",
        'third_party_tracking_no',
        'status',
        "express_fee",
        "package_fee",
        "tax_fee",
        "is_billed",
        'people',
        'show_people',
    ]

    list_display = [
        "tracking_no",
        "cn_tracking",
        "order_no",
        "weight",
        "pallet",
        "user",
        "in_no",
        "last_modified",
        "express_fee",
        "package_fee",
        "tax_fee",
        "is_billed",
        'show_people',
    ]

    list_display_links = ["tracking_no"]
    search_fields = ["tracking_no", "order_no", 'cn_tracking', 'in_no', 'pallet__pallet_no', 'goods__sku']

    def show_people(self, obj):
        if obj.people:
            return format_html(u"<a href='{url}'>{name}</a>",
                               url='/admin/addresses/people/{0}/change/'.format(obj.people.id), name=obj.people.name)
        else:
            return '-'

    show_people.allow_tags = True

class TaxItemAdmin(admin.ModelAdmin):
    class Meta:
        model = TaxItem


class WaybillStatusEntryAdmin(admin.ModelAdmin):
    class Meta:
        model = WaybillStatusEntry

    search_fields = ['order_index', 'name', 'description']
    list_display = ['order_index', 'name', 'description']


class LocationAdmin(admin.ModelAdmin):
    class Meta:
        model = Location

    search_fields = ['name', 'short_name', 'address']
    list_display = ['name', 'short_name', 'address']


class CnTrackingCreateLogAdmin(admin.ModelAdmin):
    class Meta:
        model = CnTrackingCreateLog

    search_fields = ['us_tracking', 'cn_tracking', 'msg']
    list_display = ['us_tracking', 'cn_tracking', 'msg', 'status', 'channel', 'create_dt']


class ExceptionRecordAdmin(admin.ModelAdmin):
    class Meta:
        model = ExceptionRecord

    search_fields = ['waybill__tracking_no', 'remark']
    list_display = [
        'remark',
        'user',
        'create_dt',
        'area',
        'value',
        'qty',
        'description']
    raw_id_fields = ('waybill',)


admin.site.register(Waybill, WaybillAdmin)
admin.site.register(TaxItem, TaxItemAdmin)
admin.site.register(Good)
admin.site.register(SrcLoc)
admin.site.register(WaybillStatusEntry, WaybillStatusEntryAdmin)
admin.site.register(CnTrackingCreateLog, CnTrackingCreateLogAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(ExceptionRecord, ExceptionRecordAdmin)
admin.site.register(ExceptionRecordImage)
admin.site.register(Currency)
