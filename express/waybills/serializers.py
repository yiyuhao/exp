# -*- coding: utf-8 -*
from __future__ import unicode_literals

from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Waybill, Good, WaybillStatusEntry, WaybillStatus, Location
from rest_framework.validators import UniqueValidator
from .validators import *


class UserSerializer(serializers.HyperlinkedModelSerializer):
    waybills = serializers.HyperlinkedRelatedField(many=True, view_name='waybill-detail', read_only=True)

    class Meta:
        model = User
        fields = ('url', 'id', 'username', 'waybills')


class WaybillStatusEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = WaybillStatusEntry
        fields = ('id', 'order_index', 'name')


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'name', 'address')


class WaybillStatusSerializer(serializers.HyperlinkedModelSerializer):
    status = serializers.CharField(source='status.name')
    location = serializers.ReadOnlyField(source='location.name')
    user = serializers.ReadOnlyField(source='user.username')
    create_dt = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = WaybillStatus
        fields = ('status', 'location', 'create_dt', 'user')


class GoodSerializer(serializers.HyperlinkedModelSerializer):
    waybill = serializers.HyperlinkedRelatedField(view_name='waybill-detail', read_only=True)

    class Meta:
        model = Good
        fields = ('url', 'waybill', 'cat1', 'cat2', 'brand', 'description', 'quantity',
                  'unit_price', 'unit_weight', 'remark', 'english_name', 'spec', 'unit', 'sku', 'hs_type', 'hs_type_no')


class WaybillSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    goods = GoodSerializer(many=True)
    status_set = WaybillStatusSerializer(many=True, read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name='waybill-detail', read_only=True)

    class Meta:
        model = Waybill
        fields = [
            'url', 'id', 'user', 'tracking_no', 'cn_tracking', 'order_no', 'weight', 'goods', 'pallet', 'status_set',
            'recv_province', 'recv_city', 'recv_area', 'recv_address', 'recv_zipcode', 'recv_name', 'recv_mobile',
            'recv_phone', 'order_no', 'remark', 'send_name', 'send_mobile', 'send_address', 'init_loc', 'person_id']

    def create(self, validated_data):
        goods_data = validated_data.pop('goods')
        waybill = Waybill.objects.create(**validated_data)
        for good_data in goods_data:
            Good.objects.create(waybill=waybill, **good_data)
        return waybill

    # Delete all instance.goods.all(), then using  validated_data to create new good list
    def update(self, instance, validated_data):
        goods_data = validated_data.pop('goods')

        for good in instance.goods.all():
            good.delete()

        for good_data in goods_data:
            Good.objects.create(waybill=instance, **good_data)

        return super(WaybillSerializer, self).update(instance, validated_data)


class GoodAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Good
        fields = ['hs_type', 'brand', 'description', 'quantity', 'unit_weight']


class WaybillAuditSerializer(serializers.ModelSerializer):
    goods = GoodAuditSerializer(many=True)
    user = serializers.ReadOnlyField(source='user.username')
    status = serializers.CharField(read_only=True)  # serializers.SerializerMethodField()
    cn_tracking = serializers.CharField(read_only=True)
    weight = serializers.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        model = Waybill
        fields = ["id", "tracking_no", "user", "goods", "status", "cn_tracking", "weight"]


class GoodDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Good
        fields = ['brand', 'description', 'quantity', 'img_url', 'shelf_no', 'sku']


class WaybillDetailSerializer(serializers.ModelSerializer):
    goods = GoodDetailSerializer(many=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Waybill
        fields = ["id", "tracking_no", "goods", "status", "cn_tracking", 'shelf_no']


class YHCCreateResponseDataSerializer(serializers.Serializer):
    ReferenceOrderDetailNo = serializers.CharField(required=False, allow_null=True, allow_blank=True, )
    OrderDetailNo = serializers.CharField(required=False, allow_null=True, allow_blank=True, )
    ReferenceInboundGroup = serializers.CharField(required=False, allow_null=True, allow_blank=True, )
    InboundOrderNo = serializers.CharField(required=False, allow_null=True, allow_blank=True, )
    ReferenceOutboundGroup = serializers.CharField(required=False, allow_null=True, allow_blank=True, )
    OutboundOrderNo = serializers.CharField(required=False, allow_blank=True, )  # YHC tracking_no
    IsSuccess = serializers.BooleanField(required=False)
    ErrCode = serializers.IntegerField(required=False, allow_null=True)
    ErrMessage = serializers.CharField(required=False, allow_null=True)

    def update_third_party_trackking(self):
        if self.is_valid():
            if self.OutboundOrderNo:
                waybill = Waybill.objects.get(tracking_no=self.ReferenceOrderDetailNo)
                waybill.third_party_tracking_no = self.OutboundOrderNo
                waybill.save()


class YHCCreateResponseSerializer(serializers.Serializer):
    code = serializers.IntegerField(required=False)
    msg = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    data = YHCCreateResponseDataSerializer(required=False, many=True, allow_null=True)


class GoodCreateSerializer(serializers.ModelSerializer):
    unit_weight = serializers.DecimalField(decimal_places=2, label='单位磅重', max_digits=5, min_value=0.0)
    unit_price = serializers.DecimalField(decimal_places=2, label='单价', max_digits=7, min_value=0.1)
    spec = serializers.CharField(allow_blank=True, label='规格型号', max_length=100)
    brand = serializers.CharField(label='品牌', max_length=100)
    quantity = serializers.IntegerField(label='个数', max_value=32767, min_value=1)
    hs_type = serializers.CharField(allow_blank=True, label='海关类别', max_length=30, required=False)
    hs_type_no = serializers.CharField(allow_blank=True, label='海关类别编码', max_length=20, required=False)
    sku = serializers.CharField(allow_blank=True, label='条码', max_length=80, required=False)
    description = serializers.CharField(label='描述', max_length=300, required=False)
    english_name = serializers.CharField(allow_blank=True, label='英文名', max_length=100, required=False)
    unit = serializers.CharField(allow_blank=True, label='单位', max_length=10, required=False)
    remark = serializers.CharField(max_length=150, allow_blank=True, label=u'备注', required=False)
    img_url = serializers.CharField(allow_blank=True, label='图片URL', max_length=300, required=False)

    class Meta:
        model = Good
        fields = [
            'unit_weight', 'unit_price', 'spec', 'brand', 'quantity', 'hs_type', 'hs_type_no', 'sku', 'description',
            'english_name', 'unit', 'remark', 'img_url', 'order_no', 'shelf_no'
        ]


class WaybillCreateSerializer(serializers.ModelSerializer):
    goods = GoodCreateSerializer(many=True, allow_null=False)
    # tracking_no = serializers.py.CharField(validators=[UniqueValidator(queryset=Waybill.objects.all())])

    weight = serializers.DecimalField(max_digits=5, decimal_places=2, validators=[positive])
    recv_province = serializers.CharField(label='省', max_length=10)
    recv_city = serializers.CharField(label='市', max_length=20)
    recv_area = serializers.CharField(label='区县', max_length=20, allow_blank=True)
    recv_address = serializers.CharField(label='地址', max_length=100)
    recv_zipcode = serializers.CharField(label='邮编', max_length=15)
    recv_name = serializers.CharField(label='收件人', max_length=30)
    recv_mobile = serializers.CharField(label='手机', max_length=30, validators=[cellphone])
    send_name = serializers.CharField(allow_blank=True, label='发件人', max_length=30, required=False)
    send_mobile = serializers.CharField(allow_blank=True, label='发件人电话', max_length=30, required=False)
    send_address = serializers.CharField(allow_blank=True, label='发件人地址', max_length=100, required=False)
    order_no = serializers.CharField(allow_blank=True, label='商家订单号', max_length=100, required=False)
    remark = serializers.CharField(allow_blank=True, label='备注', max_length=150, required=False)
    person_id = serializers.CharField(allow_blank=True, label='身份证号', max_length=20, required=False)
    user = serializers.PrimaryKeyRelatedField(label='用户', queryset=User.objects.all(), required=False)
    cn_tracking = serializers.CharField(allow_null=True, label='国内单号', max_length=100,
                                        required=False, validators=[UniqueValidator(queryset=Waybill.objects.all())])
    in_no = serializers.CharField(allow_blank=True, label='建单批次', max_length=30, required=False)
    # is_self_define = serializers.py.BooleanField(label='是否自定义单号', required=False)
    shelf_no = serializers.CharField(allow_blank=True, label='货架号', max_length=60, required=False)

    class Meta:
        model = Waybill
        fields = [
            'tracking_no', 'weight', 'init_loc', 'recv_province', 'recv_city', 'recv_area',
            'recv_address', 'recv_zipcode', 'recv_name', 'recv_mobile', 'send_name',
            'send_mobile', 'send_address', 'order_no', 'remark', 'person_id', 'goods', 'user', 'cn_tracking', 'in_no',
            'is_self_define', 'src_loc', 'channel', 'shelf_no']

    def create(self, validated_data):
        goods_data = validated_data.pop('goods')
        waybill = Waybill.objects.create(**validated_data)

        for good_data in goods_data:
            Good.objects.create(waybill=waybill, **good_data)

        return waybill


class WaybillCreateResponseSerializer(serializers.Serializer):
    code = serializers.BooleanField()
    msg = serializers.CharField(max_length=100, allow_blank=True)
    init_loc_id = serializers.IntegerField(allow_null=True)
    tracking_no = serializers.CharField(allow_null=True)
    order_no = serializers.CharField(allow_null=True)
    link = serializers.CharField(allow_blank=True)


class WaybillBulkCreateResponseSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    msg = serializers.CharField(max_length=100, allow_blank=True)
    data = WaybillCreateResponseSerializer(many=True)


class WaybillRevertErrorSerializer(serializers.Serializer):
    tracking_no = serializers.CharField(allow_null=False, allow_blank=False, label='运单号', max_length=100)
    goods = GoodCreateSerializer(many=True, allow_null=False)


'''
from waybills.models import *
from waybills.serializers.py import *
from rest_framework.renderers import JSONRenderer

o = {'code':1, 'msg' :"", 'init_loc_id':1, 'tracking_no':"abcd"}
o1 = {'code':0, 'msg' :"", 'init_loc_id':1, 'tracking_no':None}
wr =WaybillCreateResponseSerializer(data=o)
wr1 =WaybillCreateResponseSerializer(data=o1)

b = {'code':1, 'msg' :"", 'data':[o,o1]}

wb=WaybillBulkCreateResponseSerializer(data=b)

import re
pattern = re.compile("^([A-Za-z][0-9]+)+$")
pattern.match(string)

from waybills.models import *
from waybills.serializers.py import *
from rest_framework.renderers import JSONRenderer
import json

d = json.loads('{"tracking_no":"JH17010100002","weight":"-1","init_loc_id":1,"recv_province":"北京市","recv_city":"北京市","recv_area":"东城区","recv_address":"胡同里大街","recv_zipcode":"12321","recv_name":"张三","recv_mobile":"1380001233","send_name":"Mary Chang","send_mobile":"899123200023","send_address":"13  Garabedian Dr","order_no":"","remark":"","person_id":"","goods":[{"unit_weight":"2.00","unit_price":"15.00","spec":"","brand":"coach","quantity":1,"hs_type":"","hs_type_no":"","sku":"8886","description":"包","english_name":"","unit":"","remark":""}]}')
o =  {'user': User.objects.get(username='yi')}
w = WaybillCreateSerializer(data=d, context=o)


o =  {'user': User.objects.get(username='yi')}
d = json.loads('[{"tracking_no":"JH17010100002","weight":"2","init_loc_id":1,"recv_province":"北京市","recv_city":"北京市","recv_area":"东城区","recv_address":"胡同里大街","recv_zipcode":"12321","recv_name":"张三","recv_mobile":"1380001233","send_name":"Mary Chang","send_mobile":"899123200023","send_address":"13  Garabedian Dr","order_no":"","remark":"","person_id":"","goods":[{"unit_weight":"2.00","unit_price":"15.00","spec":"男士手包 ","brand":"coach","quantity":1,"hs_type":"","hs_type_no":"","sku":"8886","description":"包","english_name":"","unit":"","remark":""}]},{"tracking_no":"JH17010100002","weight":"-1","init_loc_id":1,"recv_province":"北京市","recv_city":"北京市","recv_area":"东城区","recv_address":"胡同里大街","recv_zipcode":"12321","recv_name":"张三","recv_mobile":"1380001233","send_name":"Mary Chang","send_mobile":"899123200023","send_address":"13  Garabedian Dr","order_no":"","remark":"","person_id":"","goods":[{"unit_weight":"2.00","unit_price":"15.00","spec":"","brand":"coach","quantity":1,"hs_type":"","hs_type_no":"","sku":"8886","description":"包","english_name":"","unit":"","remark":""}]}]')
w = WaybillCreateSerializer(many=True, data=d, context=o)

err_response_data = []
for (e, input) in  zip(w.errors, w.initial_data):
    a = {}
    a["tracking_no"] = input["tracking_no"]
    a["code"] = 0 if len(e.keys()) == 0 else 1
    a["msg"]= e
    err_response_data.append(a)


d = json.loads('{"tracking_no":"JH17010199999","weight":"2","init_loc_id":1,"recv_province":"北京市","recv_city":"北京市","recv_area":"东城区","recv_address":"胡同里大街","recv_zipcode":"12321","recv_name":"张三","recv_mobile":"1380001233","send_name":"Mary Chang","send_mobile":"899123200023","send_address":"13  Garabedian Dr","order_no":"","remark":"","person_id":"","goods":[{"unit_weight":"2.00","unit_price":"15.00","spec":"nanbao","brand":"coach","quantity":1,"hs_type":"","hs_type_no":"","sku":"8886","description":"包","english_name":"","unit":"","remark":""}]}')

listSerializer = WaybillCreateSerializer(data=[d],  many=True)
'''
