# -*- coding: utf-8 -*

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['name', 'person_id', 'province', 'city', 'mobile', 'order_no', 'is_sent']


class OrderUpsertResultResponseSerializer(serializers.Serializer):
    '''
    code
    0 success
    1 error
    2 system error
    '''
    code = serializers.BooleanField()
    msg = serializers.CharField(max_length=100, allow_blank=True)
    order_no = serializers.CharField(allow_null=True)


class OrderUpsertResponseSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    msg = serializers.CharField(max_length=100, allow_blank=True)
    data = OrderUpsertResultResponseSerializer(many=True)
