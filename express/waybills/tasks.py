# coding=utf-8
# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task

from addresses.models import People
from express.wms_api import *
from pallets.models import *
from waybills.models import Waybill, QFTracking, WaybillStatusEntry, WaybillStatus, Currency
from express.ludigang_api import *
from express.yunda_api import *


@shared_task
def wms_order_send_out(tracking_no, username):
    return notify_order_send_out(tracking_no, username)


@shared_task
def wms_push_person_id(tracking_no, name, person_id, mobile):
    return push_person_id(tracking_no, name, person_id, mobile)


@shared_task
def fetch_person_id():
    cnt = 0
    qs = Waybill.objects.filter(status__name__in=['已建单', '已审核']).filter(person_id__exact='').filter(
        channel__name__in=CH_LIST_REQUIRED_PERSON_ID)
    total = qs.count()
    for w in qs:
        res = get_person_id_from_wms(w.tracking_no)
        if res['code'] == 1:
            w.person_id = res['person_id']
            w.recv_name = res['name']
            w.recv_mobile = res['mobile']
            w.save()
            if not People.objects.filter(name=res['name'], mobile=res['mobile']).exists():
                People.objects.create(name=res['name'], id_no=res['person_id'], mobile=res['mobile'])
            if w.person_id and w.status.name == '已建单':
                uploaded_person_id = WaybillStatusEntry.objects.get(name='已传身份证')
                WaybillStatus.objects.create(waybill=w, status=uploaded_person_id)
            cnt += 1
    return {"total": total, "succ": cnt, 'fail': total - cnt}


@shared_task
def fetch_cn_tracking_yunda(w):
    if not w.cn_tracking and w.status.name == CH7:
        final_result = 'fail'
        check_code = ''
        check_msg = ''
        cn_tracking = ''
        create_code, create_msg = create(w)
        if create_code == u'0001':
            check_code, check_msg, cn_tracking = getYunda(w.tracking_no)
            if check_code == u'0001':
                QFTracking.objects.create(tracking_no=cn_tracking, waybill=w, is_used=True)
                w.cn_tracking = cn_tracking
                w.save()
                final_result = 'succ'
        return {'tracking_no': w.tracking_no, 'create_code': create_code, 'create_msg': create_msg,
                'check_code': check_code, 'check_msg': check_msg, 'cn_tracking': cn_tracking,
                'final_result': final_result}


@shared_task
def Auto_fetch_cn_tracking_CH14():
    cnt = auto_create()
    return {'succ_cnt': cnt}


@shared_task
def push_weight_to_wms(goods_no, weight, fee, tracking_no, tax):
    result = update_weight(goods_no, weight, fee, tracking_no, tax)
    return result


@shared_task
def fetch_usd_to_cnh_rate():
    qs = Currency.objects.filter(create_dt=timezone.now().date())
    if qs.count() > 0:
        return
    else:
        r = fetch_usd_cnh()
        Currency.objects.create(rate=r)
        update_currency(r, timezone.now().date())
