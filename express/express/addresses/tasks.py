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
            process_waybill_people(w)
            w = Waybill.objects.get(id=w.id)
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
    try:
        w = Waybill.objects.get(tracking_no=tracking_no)
        # 搜索系统看是否存在用户的身份证信息
        process_waybill_people(w)

        if not w.person_id:
            w.sms_notify_times += 1
            w.save()
            return send_sms_person_id_1(mobile, name, tracking_no)
        else:
            if w.channel.name == 'K2' and w.people and not w.people.id_card_front:
                w.sms_notify_times += 1
                w.save()
                return send_sms_upload_id_card(mobile, tracking_no, name)
            return None
    except:
        pass


def process_waybill_has_person_id(w):
    p = People.objects.filter(id_no=w.person_id).first()
    if p:
        w.people = p
        w.save()
    else:
        p = People.objects.create(name=w.recv_name, mobile=w.recv_mobile, id_no=w.person_id, status=1)
        w.people = p
        w.save()


def process_waybill_has_no_person_id(w):
    p = People.objects.filter(mobile=w.recv_mobile).filter(name=w.recv_name).first()
    if p:
        w.person_id = p.id_no
        w.people = p
        w.save()
        if w.status.name == '已建单':
            uploaded_person_id = WaybillStatusEntry.objects.get(name='已传身份证')
            WaybillStatus.objects.create(waybill=w, status=uploaded_person_id)
            try:
                wms_push_person_id.delay(w.tracking_no, w.recv_name, w.person_id, w.recv_mobile)
            except:
                pass


def process_waybill_people(w):
    if w.person_id:
        process_waybill_has_person_id(w)
    else:
        process_waybill_has_no_person_id(w)


def process_waybill_people_batch(in_no):
    qs = Waybill.objects.filter(in_no=in_no)
    for w in qs:
        process_waybill_people(w)


@shared_task
def notify_user_upload_person_info2_batch2(in_no):
    # 先扫描一遍系统
    process_waybill_people_batch(in_no)

    # 筛选出需要发短信的
    succ_cnt = 0
    errs = []
    qs = Waybill.objects.filter(in_no=in_no).filter(
        Q(person_id__exact='') | Q(people__id_card_backside__isnull=True) | Q(people__id_card_backside__iexact=''))
    to_be_sent_new = {}
    to_be_sent_pic = {}
    for w in qs:
        if not w.person_id:
            to_be_sent_new[w.recv_mobile] = (w.recv_name, w.tracking_no)
            w.sms_notify_times += 1
        else:
            if w.channel.name == 'K2' and not w.people.id_card_front:
                to_be_sent_pic[w.recv_mobile] = (w.recv_name, w.tracking_no)
                w.sms_notify_times += 1
        w.save()

    for mobile in to_be_sent_new:
        name, tracking = to_be_sent_new[mobile][0], to_be_sent_new[mobile][1]
        try:
            send_sms_person_id_1(mobile, name, tracking)
            succ_cnt += 1
        except Exception as e:
            errs.append({'tracking': tracking, 'code': e.message})

    for mobile in to_be_sent_pic:
        name, tracking = to_be_sent_pic[mobile][0], to_be_sent_pic[mobile][1]
        try:
            send_sms_upload_id_card(mobile, tracking, name)
            succ_cnt += 1
        except Exception as e:
            errs.append({'tracking': tracking, 'code': e.message})

    return {'total': len(to_be_sent_new) + len(to_be_sent_pic), 'succ_cnt': succ_cnt, 'errors': errs}


def searchForPersonId(w):
    p = People.objects.filter(mobile=w.recv_mobile).filter(name=w.recv_name).first()
    if p:
        w.person_id = p.id_no
        w.people = p
        w.save()

        if w.status.name == '已建单':
            uploaded_person_id = WaybillStatusEntry.objects.get(name='已传身份证')
            WaybillStatus.objects.create(waybill=w, status=uploaded_person_id)
            try:
                wms_push_person_id.delay(w.tracking_no, w.recv_name, w.person_id, w.recv_mobile)
            except:
                pass
    return w


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


def send_sms_no_pic_helper_has_people(to_be_sent, p, tracking_no):
    if not p.id_card_front:
        to_be_sent[p.mobile] = (p.name, tracking_no)


def send_sms_no_pic_helper_without_people(to_be_sent, w):
    to_be_sent[w.recv_mobile] = (w.recv_name, w.tracking_no)
    # Try to add people field to waybill
    if not People.objects.filter(mobile=w.recv_mobile).filter(name=w.recv_name).exists():
        try:
            p = People.objects.create(mobile=w.recv_mobile, name=w.recv_name, id_no=w.person_id)
            w.people = p
            w.save()
        except:
            pass


@shared_task
def send_sms_no_pic():
    qs = Waybill.objects.filter(channel__name='K2').filter(Q(status__order_index__lte=109),
                                                           Q(status__order_index__gte=2),
                                                           Q(sms_notify_times__lt=4)).filter(
        Q(people__isnull=True) | Q(people__id_card_front__isnull=True) | Q(people__id_card_front__exact=''))
    # print qs.count()
    to_be_sent = {}
    for w in qs:
        if w.people:
            send_sms_no_pic_helper_has_people(to_be_sent, w.people, w.tracking_no)
        else:
            p = People.objects.filter(mobile=w.recv_mobile).filter(name=w.recv_name).first()
            w.people = p
            w.save()
            if p:
                send_sms_no_pic_helper_has_people(to_be_sent, p, w.tracking_no)
            else:
                send_sms_no_pic_helper_without_people(to_be_sent, w)
            w.sms_notify_times += 1
            w.save()
    for mobile in to_be_sent:
        # print mobile, to_be_sent[mobile][0], to_be_sent[mobile][1]
        send_sms_upload_id_card(mobile, to_be_sent[mobile][1], to_be_sent[mobile][0])


@shared_task
def send_sms_no_pic_ab(air_waybill):
    qs = Waybill.objects.filter(Q(pallet__air_waybill__air_waybill_no=air_waybill),
                                Q(status__order_index__lte=109),
                                Q(status__order_index__gte=2)).filter(
        Q(people__isnull=True) | Q(people__id_card_front__isnull=True) | Q(people__id_card_front__exact=''))

    for w in qs:
        if not w.people:
            p = People.objects.filter(mobile=w.recv_mobile).filter(name=w.recv_name).first()
            if p:
                w.people = p
                w.save()

    qs = Waybill.objects.filter(Q(pallet__air_waybill__air_waybill_no=air_waybill),
                                Q(status__order_index__lte=109),
                                Q(status__order_index__gte=2)).filter(
        Q(people__isnull=True) | Q(people__id_card_front__isnull=True) | Q(people__id_card_front__exact=''))

    to_be_sent = {}
    for w in qs:
        if w.people:
            send_sms_no_pic_helper_has_people(to_be_sent, w.people, w.tracking_no)
        else:
            p = People.objects.filter(mobile=w.recv_mobile).filter(name=w.recv_name).first()
            w.people = p
            w.save()
            if p:
                send_sms_no_pic_helper_has_people(to_be_sent, p, w.tracking_no)
            else:
                send_sms_no_pic_helper_without_people(to_be_sent, w)
            w.sms_notify_times += 1
            w.save()
    for mobile in to_be_sent:
        # print mobile, to_be_sent[mobile][0], to_be_sent[mobile][1]
        send_sms_upload_id_card(mobile, to_be_sent[mobile][1], to_be_sent[mobile][0])
