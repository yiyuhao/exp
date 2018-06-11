# -*- coding: utf-8 -*
import re

from rest_framework import serializers


def positive(value):
    if value <=0:
        raise serializers.ValidationError('重量必须大于0')

def loc_id_validate(value):
    if value not in [1, 2]:
        raise serializers.ValidationError('请选择正确的集运仓ID')

def recv_province_validate(value):
    if value not in [""]:
        raise serializers.ValidationError('请填写正确的省份')

def cellphone(value):
    if not re.match(r"[0-9]{11}", value):
        raise serializers.ValidationError('请填写11位数的手机号')

