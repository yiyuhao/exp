# coding=utf-8
from __future__ import unicode_literals
from django.db import transaction
from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from addresses.models import ExpressMark
from emanage.permissions import IsStaff
from waybills.tasks import *
from utils import compress_id_card_image


def ch_to_num(ch):
    chmap = {
        '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
        'x': 10, 'X': 10
    }
    return chmap[ch]


def is_valid_person_id(s):
    char_list = list(s)
    num_list = [ch_to_num(ch) for ch in char_list]
    return verify_list(num_list)


def verify_list(l):
    sum = 0
    for ii, n in enumerate(l):
        i = 18 - ii
        weight = 2 ** (i - 1) % 11
        sum = (sum + n * weight) % 11

    return sum == 1


def upsert_person_info(name, person_id, mobile, id_card_front, id_card_backside):
    if not People.objects.filter(name=name, mobile=mobile).exists():
        p = People.objects.create(name=name, id_no=person_id, mobile=mobile, id_card_front=id_card_front,
                                  id_card_backside=id_card_backside)
    else:
        p = People.objects.filter(name=name, mobile=mobile).first()
        p.person_id = person_id
        p.id_card_front = id_card_front
        p.id_card_backside = id_card_backside
        p.save()
    try:
        compress_id_card_image(p)
    except:
        pass
    return p


@api_view(['POST'])
@permission_classes([AllowAny])
def upload_person_id(request):
    name = request.data.get('name', '').replace(" ", "").strip()
    person_id = request.data.get('person_id', '').replace(" ", "").strip()
    mobile = request.data.get('mobile', '').replace(" ", "").strip()
    tracking_no = request.data.get('tracking_no', '')
    is_wms = request.data.get('is_wms', False)  # 给定参数表明是wms, 则不做wms推送
    shelf_no = request.data.get('shelf_no', '').strip()
    id_card_front = request.FILES.get('id_card_front')
    id_card_backside = request.FILES.get('id_card_backside')
    shelf_obj = request.data.get('shelf_obj', '').strip()

    if shelf_obj:
        shelf_obj = json.loads(shelf_obj)

    if not all(u'\u4e00' <= char <= u'\u9fff' for char in name) \
            or u'先生' in name \
            or u'小姐' in name \
            or u'太太' in name \
            or u'同学' in name \
            or u'女士' in name:
        return Response(data={'succ': False, 'msg': "请如实填写中文姓名"},
                        content_type="application/json")

    if len(mobile) != 11:
        return Response(data={'succ': False, 'msg': "请输入11位手机号码"},
                        content_type="application/json")

    if not is_valid_person_id(person_id):
        return Response(data={'succ': False, 'msg': "请输入正确的身份证号码"},
                        content_type="application/json")

    if name and person_id and mobile:
        msg = "信息提交成功"
        people = upsert_person_info(name, person_id, mobile, id_card_front, id_card_backside)

        if tracking_no and Waybill.objects.filter(tracking_no=tracking_no).exists():
            w = Waybill.objects.get(tracking_no=tracking_no)
            w.people = people
            w.save()
            in_pallet = WaybillStatusEntry.objects.get(name='打板中')
            is_no_person_id = not w.person_id
            if w.status.order_index < in_pallet.order_index:
                w.person_id = person_id
                w.recv_name = name
                if shelf_no:
                    w.shelf_no = shelf_no
                w.save()
                if is_no_person_id and w.status.name == u'已建单':
                    uploaded_person_id = WaybillStatusEntry.objects.get(name='已传身份证')
                    WaybillStatus.objects.create(waybill=w, status=uploaded_person_id)
                if shelf_obj:
                    bind_shelf_no_to_goods(w, shelf_obj)
                try:
                    if not is_wms:
                        wms_push_person_id.delay(tracking_no, name, person_id, mobile)
                except:
                    pass

        else:
            qs = Waybill.objects.filter(recv_mobile=mobile).filter(recv_name=name).filter(status__name=u'已建单').filter(
                person_id__exact='')
            for w in qs:
                if not w.person_id and w.status.name == u'已建单':
                    w.person_id = person_id
                    w.people = people
                    w.save()
                    uploaded_person_id = WaybillStatusEntry.objects.get(name='已传身份证')
                    WaybillStatus.objects.create(waybill=w, status=uploaded_person_id)

        return Response(data={'succ': True, 'msg': msg},
                        content_type="application/json")
    else:
        return Response(data={'succ': False, 'msg': "姓名, 手机和身份证号不能为空"},
                        content_type="application/json")


@api_view(['POST'])
@permission_classes([AllowAny])
def assert_person_with_mobile_last_four(request):
    tracking_no = request.data.get('tracking_no', '')
    mobile_last_four = request.data.get('mobile_last_four', '')
    if Waybill.objects.filter(tracking_no=tracking_no).exists():
        w = Waybill.objects.get(tracking_no=tracking_no)
        if w.recv_mobile[-4:] == mobile_last_four:
            return Response(data={'succ': True, 'msg': "验证成功", "mobile": w.recv_mobile, "name": w.recv_name,
                                  "tracking_no": w.tracking_no}, content_type="application/json")
        else:
            return Response(data={'succ': False, 'msg': "验证失败, 手机号后四位不匹配"}, content_type="application/json")
    return Response(data={'succ': False, 'msg': "无对应运单"}, content_type="application/json")


@api_view(['POST'])
@permission_classes([AllowAny])
def assert_tracking(request):
    tracking = request.data.get('tracking', '')
    if Waybill.objects.filter(Q(tracking_no__iexact=tracking) | Q(cn_tracking__iexact=tracking)).exists():
        w = Waybill.objects.filter(Q(tracking_no__iexact=tracking) | Q(cn_tracking__iexact=tracking)).first()
        return Response(data={'succ': True, 'msg': "正在为您跳转", 'tracking_no': w.tracking_no},
                        content_type="application/json")
    return Response(data={'succ': False, 'msg': "%s 运单号不存在， 请输入正确运单号" % tracking}, content_type="application/json")


@api_view(['POST'])
@permission_classes([IsStaff])
def insert_ems_mark_view(request):
    if request.FILES['file']:
        try:
            cnt = insert_ems_mark(request.FILES['file'])
            return Response(data={"succ": True, "msg": "插入ems mark 成功", "succ_cnt": cnt, "total": cnt},
                            content_type="application/json")
        except Exception as e:
            return Response(data={"succ": False, "msg": e.message, "succ_cnt": 0, "total": 0},
                            content_type="application/json")
    else:
        return Response(data={'succ': False, 'msg': "请提供文件", "succ_cnt": 0, "total": 0},
                        content_type="application/json")


@transaction.atomic()
def insert_ems_mark(filehandle):
    sheet = filehandle.get_sheet()
    sheet.name_columns_by_row(0)
    sheet.colnames = ['province', 'city', 'area', 'mark']
    cnt = 0
    for x in sheet.to_records():
        province = x.get('province', '').strip()
        city = x.get('city', '').strip()
        area = x.get('area', '').strip()
        mark = x.get('mark', '')
        if province != '':
            ExpressMark.objects.create(province=province, city=city, area=area, ems_mark1=mark)
            cnt += 1

    return cnt
