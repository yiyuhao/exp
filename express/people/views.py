# -*- coding: utf-8 -*
from __future__ import unicode_literals

from django.db import transaction
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from emanage.permissions import IsStaff
from express import settings
from people.serializers import *
from .models import *
from waybills.models import Waybill


def validate_info(order, order_no, mobile, name):
    return True


def info_client(order):
    pass


def upload_person_id_view(request):
    if request.method == "GET":
        tracking_no = request.GET.get('m', '')
        if tracking_no and Waybill.objects.filter(tracking_no=tracking_no).exists():
            w = Waybill.objects.get(tracking_no=tracking_no)
            is_able_to_change_name = w.status.order_index < 10
            return render(request, "people/people_id_assert.html",
                          {"mobile": w.recv_mobile[:-4], "tracking_no": tracking_no,
                           'is_able_to_change_name': is_able_to_change_name})
        else:
            return render(request, "people/people_id_assert.html")
    else:
        return render(request, "people/people_id_assert.html")


@api_view(["POST"])
@permission_classes([IsStaff])
@parser_classes((JSONParser,))
@transaction.atomic
def upsert_new_order(request):
    listSerializer = OrderSerializer(data=request.data, many=True, context={'request': request})
    data = []
    all_success = True
    if listSerializer.is_valid():
        for order_data in listSerializer.validated_data:
            OrderUpsertResulResponseData = {
                "order_no": order_data.get('order_no'),
                "msg": ''
            }
            if not Order.objects.filter(order_no=order_data.get('order_no')).exists():
                serializer = OrderSerializer(data=order_data)
                if serializer.is_valid():
                    serializer.save()
                    OrderUpsertResulResponseData['code'] = 0
                else:
                    OrderUpsertResulResponseData['code'] = 1
                    OrderUpsertResulResponseData['msg'] = serializer.errors
                    all_success = False
            else:
                OrderUpsertResulResponseData['msg'] = u'订单已存在'
                OrderUpsertResulResponseData['code'] = 1
                all_success = False

            data.append(OrderUpsertResulResponseData)
            responseData = OrderUpsertResponseSerializer(data={
                "code": 0,
                'msg': u'成功' if all_success else u'部分数据有误, 正确数据已存储',
                'data': data
            })
            st = status.HTTP_200_OK
            responseData.is_valid()
            if settings.DEBUG:
                print (JSONRenderer().render(responseData.data))
            return Response(data=responseData.data, status=st, content_type="application/json")

    else:
        err_data = []
        for (e, input) in zip(listSerializer.errors, listSerializer.initial_data):
            a = {}
            a["code"] = 0 if len(e.keys()) == 0 else 1
            a["msg"] = "" if len(e.keys()) == 0 else e
            a["order_no"] = input.get("order_no", "")
            err_data.append(a)
        responseData = OrderUpsertResponseSerializer(data={
            "code": 1,
            'msg': u'建单数据检验未通过',
            'data': err_data
        })
        responseData.is_valid()
        if settings.DEBUG:
            print (JSONRenderer().render(responseData.data))
        return Response(data=responseData.data, status=status.HTTP_400_BAD_REQUEST, content_type="application/json")
