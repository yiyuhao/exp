# -*- coding: utf-8 -*

from __future__ import absolute_import, unicode_literals
from celery import shared_task

from express.utils import *
from addresses.models import *
import json

from waybills.models import Waybill, CH_LIST_REQUIRED_PERSON_ID
from waybills.tasks import *


@shared_task
def notify_user_upload_person_info_final():
    # 建单时间超过一天还没传身份证的, 发最后一次短信通知
    succ_cnt = 0
    errs = []
    qs = Waybill.objects.filter(Q(person_id__exact=''), Q(create_dt__lt=timezone.now() - timezone.timedelta(days=1)),
                                Q(status__name='已建单'), Q(sms_notify_times__lt=2))
    for w in qs:
        try:
            searchForPersonId(w)
            if not w.person_id:
                if w.sms_notify_times == 0:
                    obj = send_sms_person_id_1(w.recv_mobile, w.recv_name, w.tracking_no)
                else:
                    obj = send_sms_person_id_2(w.recv_mobile, w.recv_name, w.tracking_no)
                w.sms_notify_times += 1
                w.save()
                if obj['code'] == 0:
                    succ_cnt += 1
                else:
                    errs.append({'tracking': w.tracking_no, 'code': obj['code']})
        except Exception as e:
            errs.append({'tracking': w.tracking_no, 'code': e.message})
    return {'total': qs.count(), 'succ_cnt': succ_cnt, 'errors': errs}


@shared_task
def notify_user_upload_person_info2(mobile, name, tracking_no):
    '''to be deleted'''
    try:
        w = Waybill.objects.get(tracking_no=tracking_no)
        searchForPersonId(w)
        if not w.person_id:
            w.sms_notify_times += 1
            w.save()
            return send_sms_person_id_1(mobile, name, tracking_no)
        else:
            return None
    except:
        pass


@shared_task
def notify_user_upload_person_info2_batch(in_no):
    succ_cnt = 0
    errs = []
    qs = Waybill.objects.filter(in_no=in_no).filter(person_id__exact='')
    for w in qs:
        try:
            searchForPersonId(w)
            if not w.person_id:
                obj = send_sms_person_id_1(w.recv_mobile, w.recv_name, w.tracking_no)
                w.sms_notify_times += 1
                w.save()
                if obj['code'] == 0:
                    succ_cnt += 1
                else:
                    errs.append({'tracking': w.tracking_no, 'code': obj['code']})
        except Exception as e:
            errs.append({'tracking': w.tracking_no, 'code': e.message})
    return {'total': qs.count(), 'succ_cnt': succ_cnt, 'errors': errs}


def searchForPersonId(w):
    p = People.objects.filter(mobile=w.recv_mobile).filter(name=w.recv_name).first()
    if p:
        w.person_id = p.id_no
        if p.id_card_front:
            w.people = p
        w.save()

        if w.status.name == '已建单':
            uploaded_person_id = WaybillStatusEntry.objects.get(name='已传身份证')
            WaybillStatus.objects.create(waybill=w, status=uploaded_person_id)
            try:
                wms_push_person_id.delay(w.tracking_no, w.recv_name, w.person_id, w.recv_mobile)
            except:
                pass


@shared_task()
def notfiy_user_up_id_finish_packing(mobile, name, tracking_no):
    ''' to be deleted'''
    return send_sms4(mobile, name, tracking_no)


@shared_task
def match_person_id():
    qs = Waybill.objects.filter(person_id__iexact='').filter(status__order_index=1)
    succ = 0
    for w in qs:
        p = People.objects.filter(mobile=w.recv_mobile).filter(name=w.recv_name).first()
        if p:
            succ += 1
            w.person_id = p.id_no
            if p.id_card_front:
                w.people = p
            w.save()

            if w.status.name == '已建单':
                uploaded_person_id = WaybillStatusEntry.objects.get(name='已传身份证')
                WaybillStatus.objects.create(waybill=w, status=uploaded_person_id)
                try:
                    wms_push_person_id.delay(w.tracking_no, w.recv_name, w.person_id, w.recv_mobile)
                except:
                    pass
    return {'total': qs.count(), 'succ': succ}
