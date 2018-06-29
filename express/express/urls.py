"""express URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.views.static import serve
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from accounts.views import *
from addresses.views import upload_person_id, insert_ems_mark_view, assert_person_with_mobile_last_four, assert_tracking
from people.views import upload_person_id_view
from waybills.views import *
from pallets.views import *
from emanage.views import *
from blog.views import *
from siteconf.views import *
from waybills.views import waybills, waybill
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view
from rest_framework.authtoken import views as auth_token_views
from django.contrib.auth import views as auth_views

from express.settings import MEDIA_ROOT

schema_view = get_schema_view(title='Expresss API')

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'waybills', WaybillViewSet)
router.register(r'users', UserViewSet)
router.register(r'goods', GoodViewSet)
router.register(r'pallets', PalletViewSet)
router.register(r'waybillstatusentry', WaybillStatusEntryViewSet)
router.register(r'location', LocationViewSet)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^login/$', customer_login_view, name='login'),
    url(r'^logout/$', auth_views.logout, name='logout'),
    # url(r'^', include('django.contrib.auth.urls')),

    # rest API
    url('^schema/$', schema_view),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # url(r'^api-token-auth/$', auth_token_views.obtain_auth_token),
    url(r'^api/', include(router.urls)),
    # url(r'^api/waybill_bulk_create/$', waybill_bulk_create, name="api-bulk-create-waybill"),
    url(r'^api/waybill_bulk_create/$', waybill_bulk_create_new, name="api-bulk-create-waybill"),

    url(r'^api-ajax/waybill-checkin/$', manage_checkin_view, name='manage-check-in-ajax'),
    url(r'^api-ajax/waybill-check-form/$', manage_waybill_check_form, name='manage-waybill-form-ajax'),
    url(r'^api-ajax/waybill-detail/$', manage_waybill_detail, name='manage-waybill-detail-ajax'),
    url(r'^api-ajax/waybill-error-report-form/$', manage_waybill_error_report_form,
        name='manage-waybill-error-report-form-ajax'),
    url(r'^api-ajax/waybill-weight/$', manage_waybill_weight, name='manage-waybill-weight'),
    url(r'^api-ajax/waybill-error-report/$', manage_waybill_error_report, name='manage-waybill-error-report'),
    url(r'^api-ajax/waybill-package-to-pallet/', manage_waybill_package_to_pallet_view,
        name='manage-package-to-pallet'),
    url(r'^api-ajax/waybill-package-to-pallet2/', manage_waybill_package_to_pallet_view2,
        name='manage-package-to-pallet2'),
    url(r'^api-ajax/pallet-create/$', manage_pallet_create, name='manage-pallet-creaet-ajax'),
    url(r'^api-ajax/waybills-in-pallet-not-submit/$', get_waybills_in_pallet_not_submit,
        name='manage-waybills-in-pallet-not-submit-ajax'),
    url(r'^api-ajax/waybill-pallet-delete/(?P<pk>[0-9]+)/$', manage_waybill_pallet_delete,
        name='manage-waybill-pallet-delete'),
    url(r'^api-ajax/waybill-exist/(?P<type>[abcd])/$', manage_waybill_exist_check,
        name='manage-waybill-exist-check-ajax'),

    url(r'^api-ajax/air-waybill-create/$', manage_air_waybill_create, name='manage-air-waybill-create-ajax'),
    url(r'^api-ajax/air-waybill-send-out/(?P<pk>[0-9]+)/$', manage_air_waybill_send_out,
        name='manage-air-waybill-send-out-ajax'),
    url(r'^api-ajax/air-waybill-update-airline/(?P<pk>[0-9]+)/$', manage_air_waybill_update_airline,
        name='manage-air-waybill-update-airline-ajax'),
    url(r'^api-ajax/air-waybill-cn-deliver/(?P<pk>[0-9]+)/$', manage_air_waybill_cn_deliver,
        name='manage-air-waybill-cn-deliver-ajax'),
    url(r'^api-ajax/waybill-usps-update/$', update_waybill_usps, name='manage-waybill-usps-update-ajax'),
    url(r'^api-ajax/add-yunda/$', add_yunda_waybills, name='manage-add-yunda-ajax'),
    url(r'^api-ajax/goods/(?P<waybill_id>[0-9]+)/$', waybill_goods, name='manage-goods_detail-ajax'),

    url(r'^api-ajax/check-cn-status/$', check_cn_status_excel, name='manage-check-cn-status-ajax'),
    url(r'^api-ajax/upload-person-id/$', upload_person_id, name='manage-upload-person-id-ajax'),
    url(r'^api-ajax/assert-person/$', assert_person_with_mobile_last_four, name='manage-assert-person-ajax'),
    url(r'^api-ajax/assert-tracking/$', assert_tracking, name='manage-assert-tracking-ajax'),

    url(r'^api-ajax/get-virtual-yunda-excel/$', get_virtual_yunda_excel, name='manage-get-virtual-yunda-excel-ajax'),
    url(r'^api-ajax/update-virtual-yunda-excel/$', update_virtual_yunda_excel_view,
        name='manage-update-virtual-yunda-excel-ajax'),

    url(r'^api-ajax/mark-waybill-error/$', mark_waybill_error_view, name='manage-marl-waybill-error'),
    url(r'^api-ajax/revert-waybill-error/$', revert_waybill_error_view, name='manage-marl-waybill-error'),

    url(r'^api-ajax/get-bdt-yunda-excel/$', get_bdt_yunda_excel, name='manage-get-bdt-yunda-excel-ajax'),
    url(r'^api-ajax/get-export-q-excel/$', get_export_q_excel, name='manage-get-export-q-excel-ajax'),

    url(r'^api-ajax/get-qd-ems-excel/$', get_qd_ems_excel, name='manage-get-qd-ems-excel-ajax'),
    url(r'^api-ajax/update-cn-tracking-excel/$', update_cn_tracking_from_excel_view,
        name='manage-update-cn-tracking-excel-ajax'),
    url(r'^api-ajax/change-cn-tracking-excel/$', change_cn_tracking_from_excel_view,
        name='manage-change-cn-tracking-excel-ajax'),
    url(r'^api-ajax/change-channel-excel/$', change_channel_from_excel_view,
        name='manage-change-channel-excel-ajax'),
    url(r'^api-ajax/change-name-excel/$', change_name_from_excel_view,
        name='manage-change-name-excel-ajax'),
    url(r'^api-ajax/waybills-time/$', waybills_time,
        name='manage-waybills-time-ajax'),
    url(r'^api-ajax/waybills-send-days/$', waybills_send_days,
        name='manage-waybills-send-days-ajax'),
    url(r'^api-ajax/auto-create/$', auto_create_view, name='manage-auto-create-ajax'),

    url(r'^api-ajax/update-package-weight-excel/$', update_package_weight_from_excel_view,
        name='manage-update-package-weight-excel-ajax'),
    url(r'^api-ajax/get-labels/$', get_labels, name='manage-get-labels-ajax'),
    url(r'^api-ajax/get-waybills-cn-tracking/$', get_waybills_cn_tracking, name='manage-get-waybills-cn-tracking-ajax'),
    url(r'^api-ajax/get-waybills-bulk-print/$', manage_waybill_bulk_print_view,
        name='manage-get-waybills-bulk-print-ajax'),

    url(r'^api-ajax/insert-ems-mark-excel/$', insert_ems_mark_view, name='manage-insert-ems-mark-excel-ajax'),
    url(r'^api-ajax/bulk-print-sku/$', manage_batch_print_sku, name='manage-bulk-print-sku-ajax'),

    url(r'^api-ajax/air-waybill-fee/$', air_waybill_fee_excel_view, name='manage-air-waybill-fee-excel-ajax'),

    url(r'^api-ajax/test/$', test_api_post, name='manage-check-in-ajax'),

    url(r'^api-ajax/add-exception-record/$', manage_add_exception_record, name='manage-add-exception-record-ajax'),
    url(r'^api-ajax/get-exception-record-images/$', manage_get_exception_record_images,
        name='manage-get-exception-record-images-ajax'),
    url(r'^api-ajax/waybill-send-to-warehouse/$', waybill_send_to_warehouse,
        name='manage-waybill-send-to-warehouse-ajax'),
    url(r'^api-ajax/sifang_pdf/$', get_sifang_pdf, name='sifang-pdf-ajax'),
    url(r'^api-ajax/get-k-no-pic-excel/$', get_k_no_pid_excel, name='k-no-pic-ajax'),

    # app
    url('^$', IndexView.as_view(), name='index'),
    url(r'^accounts/profile/$', customer_profile_view, name='accounts_profile'),
    url(r'^waybills/$', waybills, name='customer_waybill_list'),
    url(r'^waybills/(?P<pk>[0-9]+)/$', waybill, name='customer_waybill_detail'),
    url(r'^waybills/create/$', waybillCreate, name='customer_waybill_create'),
    url(r'^waybills/bulk_create/$', waybillBulkCreate, name='customer_waybill_bulk_create'),
    url(r'^waybills/search/$', waybill_search_view, name='customer_waybill_search'),
    url(r'^waybills/print/(?P<pk>[0-9]+)/$', WaybillPDF.as_view(), name='customer_waybill_print'),
    url(r'^waybills/label/(?P<pk>[0-9]+)/$', WaybillLabel.as_view(), name='customer_waybill_label'),
    url(r'^waybills/small_label/(?P<pk>[0-9]+)/$', WaybillSmallLabel.as_view(), name='customer_waybill_small_label'),

    url(r'^manage/$', manage_index_view, name='manage-index'),
    url(r'^manage/performance/$', performacne_view, name='manage-performance'),
    url(r'^manage/package-time/$', package_time_view, name='manage-package-time'),
    url(r'^manage/login/$', manage_login_view, name='manage-login'),
    url(r'^manage/accounts/profile/$', manage_profile_view, name='manage-account'),
    url(r'^manage/logout/$', manage_logout_view, name='manage-logout'),
    url(r'^manage/check-in-package/$', manage_waybill_check_in_view, name='manage-waybill-check-in'),
    url(r'^manage/waybill-audit/$', manage_waybill_audit_view, name='manage-waybill-audit'),
    url(r'^manage/waybill-error-report/$', manage_waybill_error_view, name='manage-waybill-error-report'),
    url(r'^manage/pallets/create/$', manage_pallet_create_view, name='manage-pallet-create'),
    url(r'^manage/pallets/create2/$', manage_pallet_create_view2, name='manage-pallet-create2'),
    url(r'^manage/waybills/$', manage_waybills_view, name='manage-waybills'),
    url(r'^manage/waybills/print-single/$', manage_waybill_print_single_good_view,
        name='manage-waybills-print-single-good'),
    url(r'^manage/waybills/print-multi/$', manage_waybill_print_multi_goods_view,
        name='manage-waybills-print-multi-goods'),
    url(r'^manage/waybills/print-tracking/$', manage_waybill_print_tracking_view,
        name='manage-waybills-print-tracking'),
    url(r'^manage/waybills/bulk-print/$', manage_waybills_bulk_print_view, name='manage-waybills-bulk-print'),
    url(r'^manage/waybills/bulk-print-multi/$', manage_waybills_bulk_print_multiple_view,
        name='manage-waybills-bulk-print-multi'),
    url(r'^manage/waybills/change-label/$', manage_waybill_change_label_view, name='manage-waybills-change-label'),
    url(r'^manage/pallets/$', manage_pallets_view, name='manage-pallets'),
    url(r'^manage/air-waybills/$', air_waybills_view, name='manage-air-waybill-list'),
    url(r'^manage/customs/(?P<pk>[0-9]+)/$', manage_customs_files, name='manage-customs-files'),
    url(r'^manage/agents/(?P<pk>[0-9]+)/$', manage_agent_files, name='manage-agent-files'),
    url(r'^manage/id-cards-download/(?P<pk>[0-9]+)/$', manage_id_cards_files, name='manage-id-cards-files'),
    url(r'^manage/usps-file/(?P<pk>[0-9]+)/$', manage_usps_files, name='manage-usps-files'),
    url(r'^manage/both-tracking/(?P<pk>[0-9]+)/$', manage_both_tracking_files, name='manage-both-tracking-files'),
    url(r'^manage/batch-check-cn-status/$', manage_batch_export_view, name='manage-batch-check-cn-status'),
    url(r'^manage/export-waybill/$', manage_export_waybill, name='manage-export_waybill-files'),
    url(r'^manage/export-waybill-address/$', manage_export_waybill_address_info,
        name='manage-export_waybill-address-files'),
    url(r'^manage/custom-data/$', custom_data, name='manage-custom-data'),
    url(r'^manage/exception-list/$', manage_exception_list_view, name='manage-exception-list'),
    url(r'^manage/exception-list/delete-record/(?P<pk>[0-9]+)$', manage_delete_exception_record, name='manage-exception-list-delete-record'),
    url(r'^manage/review-id-image/$', manage_id_card_image_view, name='review-id-image'),
    url(r'^manage/waybill-send-to-warehouse/$', manage_waybill_send_to_warehouse_view,
        name='manage-waybill-send-to-warehouse'),
    url(r'^manage/waybill-check-detail/$', manage_waybill_detail_view, name='manage-waybill-check-detail'),

    url(r'^api-test/$', api_test, name='api-test'),

    url(r'^about/$', about_view, name='about'),
    url(r'^service/$', service_view, name='service'),
    url(r'^blogs/$', blogs_view, name='blog-lists'),
    url(r'^blogs/(?P<pk>[0-9]+)/$', blog_detail_view, name='blog-detail'),

    url(r'^manage/customs2/$', manage_customs_files2, name='manage-customs-files2'),
    # url(r'^manage/customs-goods/$', manage_customs_goods, name='manage-customs-goods'),

    url(r'u/$', upload_person_id_view, name='upload-person-id'),
    # url(r'^manage/customs2/$', manage_customs_files2, name='manage-customs-files2'),
    # url(r'^hard-code/$', hard_code, name='hard-code'),

    url(r'^barcode/$', barcode_view, name='barcode-view'),
    url(r'^barcode/(?P<barcode>.+)$', barcode, name='barcode'),

    url(r'^media/(?P<path>.*)$', serve, {"document_root": MEDIA_ROOT}),

    url(r'^ckeditor/', include('ckeditor_uploader.urls'))

]
if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
