# -*- coding: utf-8 -*


from __future__ import unicode_literals

import random

import sys
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
import uuid
from django.db.models import F
from django.db.models import Q
from django.db.models import Sum
from django.db.models.sql import AND
from django.urls import reverse
from django.utils.encoding import smart_unicode
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db.models.aggregates import Max, Count
from accounts.models import Customer, Employee
from addresses.models import People
from express.utils import remove_sheng_shi_zizhiqu, check_cn_status, CN_WAYBILL_STATUS, get_yhc_status, toTZDatetime, \
    fetch_usd_cnh
from pypinyin import lazy_pinyin
import json
import pytz
from pallets.models import *

TRACKING_NO_PREFIX = 'AB'
TIMESTAMP_LEN = 6
SERIAL_NO_LEN = 5
TIMESTAMP_START = len(TRACKING_NO_PREFIX)
SERIAL_NO_START = TIMESTAMP_START + TIMESTAMP_LEN
TRACKING_NO_LEN = len(TRACKING_NO_PREFIX) + TIMESTAMP_LEN + SERIAL_NO_LEN
LUX_BRAND = {'3.1 phillip lim', 'alexander wang', 'balenciaga', 'bally', 'ferragamo', 'fendi', 'givenchy', 'gucci',
             'hermes', 'loewe', 'love moschino', 'miu miu', 'moschino', 'proenza schouler', 'salvatore ferragamo',
             'see by chloe', 'tod\'s', 'valentino', 'versace', 'burberry', 'prada', 'celine', 'dior',
             'saint laurent', 'ysl', 'bottega veneta'}

RMB_RATE = Decimal(6.65)
DISCOUNT = Decimal(0.5 * 1.3)


# Create your models here.
class Waybill(models.Model):
    # 渠道
    channel = models.ForeignKey('pallets.Channel', related_name='waybills', null=True, blank=True, default=None,
                                on_delete=models.PROTECT, verbose_name=u'渠道')

    # 收费类别
    # charge_type = models.ForeignKey('Chargetype', related_name='waybill_type', null=True,
    # on_delete=models.PROTECT)

    # 国际单号
    tracking_no = models.CharField(unique=True, max_length=100, verbose_name=u'国际单号')

    # 国内单号
    cn_tracking = models.CharField(unique=True, max_length=100, null=True, verbose_name=u'国内单号')

    # 国内单号
    third_party_tracking_no = models.CharField(unique=True, max_length=100, null=True, verbose_name=u'第三方物流单号')

    # 商家单号
    order_no = models.CharField(max_length=100, null=True, blank=True, verbose_name=u'商家订单号')

    # 包裹重量
    weight = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=u'包裹重量')

    # 所属托盘
    pallet = models.ForeignKey('pallets.Pallet', related_name='waybills', null=True, blank=True,
                               on_delete=models.SET_NULL, verbose_name=u'所属托盘')

    # 创建用户
    user = models.ForeignKey('auth.User', related_name='waybills', on_delete=models.PROTECT, verbose_name=u'用户')

    # 备注
    remark = models.CharField(max_length=150, null=True, blank=True, verbose_name=u'备注')

    # 收件人
    recv_name = models.CharField(max_length=30, verbose_name=u'收件人')

    # 省份
    recv_province = models.CharField(max_length=20, verbose_name=u'省')

    # 市
    recv_city = models.CharField(max_length=30, verbose_name=u'市')

    # 区县
    recv_area = models.CharField(max_length=20, verbose_name=u'区县')

    # 地址
    recv_address = models.CharField(max_length=100, verbose_name=u'地址')

    # 邮编
    recv_zipcode = models.CharField(max_length=15, verbose_name=u'邮编')

    # 手机
    recv_mobile = models.CharField(max_length=30, verbose_name=u'手机')

    # 座机
    recv_phone = models.CharField(max_length=30, blank=True, null=True, verbose_name=u'电话')

    # 包裹费率
    charge_rate = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name=u'费率')

    # 创建时间
    create_dt = models.DateTimeField(auto_now_add=True, verbose_name=u'生成时间')

    # 最后修改时间
    last_modified = models.DateTimeField(auto_now=True, verbose_name=u'最后修改')

    # 标记是否是自定义单号
    is_self_define = models.BooleanField(default=False, verbose_name=u'是否自定义单号')

    #
    send_name = models.CharField(max_length=30, blank=True, verbose_name=u'发件人')

    #
    send_mobile = models.CharField(max_length=30, blank=True, verbose_name=u'发件人电话')

    #
    send_address = models.CharField(max_length=100, blank=True, verbose_name=u'发件人地址')

    #
    init_loc = models.ForeignKey('Location', verbose_name=u'初始接收地', related_name='waybill',
                                 on_delete=models.PROTECT)
    #
    in_no = models.CharField(max_length=30, blank=True, verbose_name=u'建单批次', default='')

    #
    is_print_by_manage = models.BooleanField(default=False, verbose_name=u'是否已经在出单界面打印')

    #
    person_id = models.CharField(verbose_name=u'身份证号', default='', blank=True, max_length=20)

    #
    people = models.ForeignKey('addresses.People', verbose_name=u'people', related_name='waybill',
                               on_delete=models.SET_NULL,
                               null=True, blank=True, default=None)

    #
    transaction_no = models.CharField(max_length=40, null=True, verbose_name=u'交易号')

    #
    status = models.ForeignKey('WaybillStatusEntry', related_name='waybills', verbose_name=u'状态', default=None,
                               null=True, blank=True, on_delete=models.SET_NULL)

    #
    src_loc = models.ForeignKey('SrcLoc', related_name='waybills', verbose_name=u'来源地', default=None, null=True,
                                blank=True, on_delete=models.SET_NULL)

    shelf_no = models.CharField(max_length=60, blank=True, default='', verbose_name=u'货架号')

    sms_notify_times = models.IntegerField(blank=True, default=0, verbose_name=u'短信通知次数')

    # json string
    yd_info = models.CharField(max_length=300, null=True, default=None, verbose_name='韵达信息', blank=True)

    # 身份证上传时间
    upload_person_id_dt = models.DateTimeField(verbose_name=u'身份证上传时间', null=True, blank=True, default=None)

    package_fee = models.DecimalField(verbose_name=u'打包费', decimal_places=2, max_digits=5, default=0, blank=True)

    express_fee = models.DecimalField(verbose_name=u'运费', decimal_places=2, max_digits=5, default=0, blank=True)

    tax_fee = models.DecimalField(verbose_name=u'税费', decimal_places=2, max_digits=5, default=0, blank=True)

    is_billed = models.BooleanField(verbose_name=u'已出账单', default=False, null=False, blank=False)

    def __unicode__(self):
        return self.tracking_no

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        is_new = self.id is None

        if is_new:
            loc = Customer.objects.get(user=self.user).loc
            self.init_loc = loc
            if self.person_id:
                self.upload_person_id_dt = timezone.now()
        else:
            previous = Waybill.objects.get(id=self.id)
            if not previous.person_id and self.person_id:
                self.upload_person_id_dt = timezone.now()

        super(Waybill, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                  update_fields=update_fields)

        if is_new:
            WaybillStatus.objects.create(waybill=self, status=WaybillStatusEntry.objects.filter(
                name__exact=u'已建单').first(), user=self.user)

    @classmethod
    def get_next_sys_tracking_no(cls):
        curr_timestamp = timezone.now().strftime("%Y%m%d")[2:]
        if cls.objects.filter(Q(is_self_define=False),
                              Q(tracking_no__istartswith=TRACKING_NO_PREFIX + curr_timestamp)).exists():
            last = cls.objects.filter(Q(is_self_define=False),
                                      Q(tracking_no__istartswith=TRACKING_NO_PREFIX + curr_timestamp)).order_by(
                "-tracking_no")[0]
            timestamp = last.tracking_no[TIMESTAMP_START: TIMESTAMP_START + TIMESTAMP_LEN]
            serial_no = int(last.tracking_no[SERIAL_NO_START:])
            next_serial_no = serial_no + 1
            if timestamp != curr_timestamp:
                next_serial_no = 1
            return '%s%s%05d' % (TRACKING_NO_PREFIX, curr_timestamp, next_serial_no)
        else:
            return '%s%s%05d' % (TRACKING_NO_PREFIX, curr_timestamp, 1)

    def can_delete(self):
        return self.status_set.count() < 2

    def get_wrap_pdf(self):
        return {
            "tracking_no": self.tracking_no,
            "sender_name": self.send_name,
            "recv_name": self.recv_name,
            "total": self.goods.all().aggregate(total=Sum('quantity'))['total'],
            "detail": self.get_goods_repr(),
            "remark": '' if not self.remark else self.remark,
            "cn_tracking_no": self.cn_tracking,
            "recv_prov": self.recv_province,
            "recv_city": self.recv_city,
            "recv_area": self.recv_area,
            "recv_address": self.recv_address,
            'mobile': self.recv_mobile,
            'goods': self.get_goods_repr(),
            'weight': self.weight,
            'qty': self.get_goods_quantity(),
            'channel_name': self.channel.name,
            'zipcode': self.recv_zipcode,
            'goods2': self.get_goods_repr2(),
            'value': self.get_value(),
            'yd_info': self.yd_info
        }

    def get_yunda_obj(self):
        return {
            'order_serial_no': self.tracking_no,
            'khddh': self.tracking_no,
            'receiver': {
                'name': self.recv_name,
                'city': ','.join([self.recv_province, self.recv_city, self.recv_area]),
                'address': ','.join([self.recv_province, self.recv_city, self.recv_area]) + self.recv_address,
                'postcode': self.recv_zipcode,
                'mobile': self.recv_mobile,
            },
            'weight': self.weight,
            'wave_no': self.in_no,
            'items': [{
                'name': g.hs_type if g.hs_type else '',
                'number': g.quantity,
                'remark': ''
            } for g in self.goods.all()],
        }

    def get_sifang_obj(self):
        return {
            'ShipperOrderNo': self.tracking_no,
            'ServiceTypeCode': 'TP',
            'TerminalCode': '',
            'ConsignerName': 'HuskyEx',
            'ConsignerMobile': '8058681682',
            'ConsigneeName': self.recv_name,
            'Province': self.recv_province,
            'City': self.recv_city,
            'District': self.recv_area,
            'ConsigneeStreetDoorNo': self.recv_address,
            'ConsigneeIDNumber': self.person_id,
            'ConsigneeMobile': self.recv_mobile,
            'OrderWeight': float(self.weight),
            'ItemDeclareCurrency': 'CNY',
            'InsuranceTypeCode': '',
            'EndDeliveryType': '',
            'ITEMS': [{
                "ItemDeclareType": "01010700002",  # TODO
                "ItemBrand": "A2",
                "Specifications": g.spec if g.spec else g.description,  # TODO
                "ItemName": g.description,
                'ItemSKU': g.sku,
                'ItemQuantity': g.quantity,
                'ItemUnitPrice': float(g.unit_price),
                'PreferentialSign': 'Y'
            } for g in self.goods.all()],
        }

    def get_sifang_obj_sku(self):
        return {
            'ShipperOrderNo': self.tracking_no,
            'ServiceTypeCode': 'TP',
            'TerminalCode': '',
            'ConsignerName': 'HuskyEx',
            'ConsignerMobile': '8058681682',
            'ConsigneeName': self.recv_name,
            'Province': self.recv_province,
            'City': self.recv_city,
            'District': self.recv_area,
            'ConsigneeStreetDoorNo': self.recv_address,
            'ConsigneeIDNumber': self.person_id,
            'ConsigneeMobile': self.recv_mobile,
            'OrderWeight': float(self.weight),
            'ItemDeclareCurrency': 'CNY',
            'InsuranceTypeCode': '',
            'EndDeliveryType': '',
            'ITEMS': [{
                "ItemSKU": g.sku,  # TODO
                'ItemQuantity': g.quantity,
                'ItemUnitPrice': float(g.unit_price),
                'PreferentialSign': 'Y'
            } for g in self.goods.all()],
        }

    def get_value(self):
        result = 0
        for good in self.goods.all():
            result += good.unit_price * good.quantity
        return result * RMB_RATE * DISCOUNT

    def get_actual_value_usd(self):
        result = 0
        for good in self.goods.all():
            result += good.unit_price * good.quantity
        return result

    def get_value_rmb(self):
        result = 0
        for good in self.goods.all():
            result += good.unit_price * good.quantity
        return result * RMB_RATE

    def get_goods_repr(self):
        l = []
        for good in self.goods.all():
            l.append('[QTY: %d] %s' % (good.quantity, good.sku))
        return '\n'.join(l)

    def get_goods_repr2(self):
        l = []
        for good in self.goods.all():
            l.append('[QTY: %d] %s %s %s' % (good.quantity, good.sku, good.brand,
                                             good.hs_type if good.hs_type else good.cat2 if good.cat2 else good.description))
        return '\n'.join(l)

    def get_yhc_create_data(self):
        result = []
        w = {"ReferenceOrderDetailNo": self.tracking_no, "ReferenceInboundGroup": self.tracking_no,
             "ReferenceOutboundGroup": self.tracking_no, "DeliveryType": "SELF", "TrackingNoIn": self.tracking_no,
             "WarehouseID": 2, "Consignee": self.recv_name, "Phone": self.recv_mobile, "Province": self.recv_province,
             "City": self.recv_city, "Postcode": self.recv_zipcode, "Address1": self.recv_area + self.recv_address}

        for good in self.goods.all():
            g = {"Commodity": good.cat2, "UnitPrice": float(good.unit_price), "DeclaredValue": float(good.unit_price),
                 "Quantity": good.quantity}
            c = {}
            c.update(w)
            c.update(g)
            result.append(c)
        return result

    def is_able_to_print_out(self):
        '''
        code:
        0 能出
        1 运单不存在
        2 缺国内单号
        3 没身份证
        4 系统错误
        6 状态异常
         '''
        already_up_pid = WaybillStatusEntry.objects.get(name='已传身份证')
        error_status = WaybillStatusEntry.objects.get(name='运单异常')

        if self.status == error_status:
            return False, 6

        if self.status.order_index > already_up_pid.order_index:
            raise Exception('状态: {0}, 不允许重复出单'.format(self.status.name))

        else:
            if not self.cn_tracking:
                # 无国内单号
                if self.channel.name in CH_LIST_NOT_REQUIRED_PERSON_ID:
                    return True, 0
                else:
                    return False, 2
            else:
                # 有国内单号
                if not self.person_id:
                    # 无身份证
                    if self.channel.name in CH_LIST_NOT_REQUIRED_PERSON_ID:
                        # 不要求身份证渠道
                        return True, 0
                    else:
                        # 要求身份证渠道
                        return False, 3
                else:
                    # 有证
                    return True, 0

    @classmethod
    def get_able_to_print_query(cls):
        q = Q()
        q.add(~Q(cn_tracking__exact=''), AND)
        q.add(Q(cn_tracking__isnull=False), AND)
        # if ch_name and ch_name in CH_LIST_REQUIRED_PERSON_ID:
        q.add(~Q(person_id__exact=''), AND)
        q.add(Q(person_id__isnull=False), AND)

        return q

    @classmethod
    def get_waybill_with_skus(cls, skus, in_no, src_loc_id, channel_id, shelf_no):
        '''
        :param skus:
        :return:
        code
            0   success
            1   waybill not exist
            2   no cn_tracking
            3   no person_id
            4   system error
            5   goods not in shelf

            link
            for waybill pdf
        '''
        code = 1
        link = ""
        goods = []
        tracking_no = ""
        return_obj = None
        sent_to_warhouse_status = WaybillStatusEntry.objects.get(name='已发往集运仓')

        q = Q()
        q.add(Q(status__order_index__lt=sent_to_warhouse_status.order_index), Q.AND)
        q.add(Q(is_print_by_manage=False), Q.AND)
        if in_no:
            q.add(Q(in_no__istartswith=in_no), Q.AND)
        if src_loc_id:
            q.add(Q(src_loc__id=src_loc_id), Q.AND)
        if channel_id and int(channel_id) > 0:
            q.add(Q(channel__id=channel_id), Q.AND)
        if shelf_no:
            q.add(Q(shelf_no__icontains=shelf_no), Q.AND)
        q.add(Q(goods_num=len(skus)), Q.AND)

        if len(skus) == 1:
            q.add(Q(goods__sku=skus[0]), Q.AND)

            if Waybill.objects.annotate(goods_num=Sum('goods__quantity')).filter(q).exists():
                obj = Waybill.objects.annotate(goods_num=Sum('goods__quantity')).filter(q).order_by('-person_id',
                                                                                                    'id').first()
                code = 0
                link = reverse('customer_waybill_label', kwargs={"pk": obj.id})
                goods = ['%s x%d' % (good.sku, good.quantity) for good in obj.goods.all()]
                tracking_no = obj.tracking_no
                return_obj = obj
            else:
                code = 1
        else:
            sku_map = {}
            for sku in skus:
                if sku in sku_map:
                    sku_map[sku] += 1
                else:
                    sku_map[sku] = 1

            qs = Waybill.objects.annotate(goods_num=Sum('goods__quantity')).filter(q).distinct()
            if qs.exists():
                for obj in qs.order_by('-person_id', 'id'):
                    # 比对输入条码个数和订单条码个数
                    is_match = True
                    order_sku_map = {}
                    for good in obj.goods.all():
                        if good.sku in order_sku_map:
                            order_sku_map[good.sku] += good.quantity
                        else:
                            order_sku_map[good.sku] = good.quantity

                    if len(order_sku_map.keys()) != len(sku_map.keys()):
                        continue
                    else:
                        for k in sku_map:
                            if k not in order_sku_map or order_sku_map[k] != sku_map[k]:
                                is_match = False
                                break
                        if is_match:
                            code = 0
                            link = reverse('customer_waybill_label', kwargs={"pk": obj.id})
                            goods = ['%s x%d' % (good.sku, good.quantity) for good in obj.goods.all()]
                            tracking_no = obj.tracking_no
                            return_obj = obj
                            break
            else:
                code = 1

        return code, link, goods, tracking_no, return_obj

    def get_most_recent_status(self):
        return self.status_set.filter(create_dt__lte=timezone.now()).order_by('-id').first()

    def set_package_sent_to_center(self, user):
        sent_to_center = WaybillStatusEntry.objects.get(name=u'已发往集运仓')

        if self.status.order_index < sent_to_center.order_index:
            '''
            出面单的同时, 将运单设为发往集运仓;
            
            '''
            loc = Employee.objects.get(user=user).loc
            sent = WaybillStatus.objects.create(waybill=self, status=sent_to_center, user=user, location=loc)

            # 如果是NJ的包裹则直接入库
            # if self.src_loc.name == 'NJ':
            #     already_check_in = WaybillStatusEntry.objects.get(name='已入库')
            #     loc = Employee.objects.get(user=user).loc
            #     WaybillStatus.objects.create(waybill=self, status=already_check_in, user=user, location=loc,
            #                                  create_dt=sent.create_dt + timezone.timedelta(minutes=1))

    def get_goods_quantity(self):
        if self.goods.all().count() > 0:
            return self.goods.aggregate(total=Sum('quantity')).get('total', 0)
        else:
            return 0

    def get_goods_weight(self):
        result = 0
        for g in self.goods.all():
            result += g.unit_weight * g.quantity
        return result

    def get_goods_content(self):
        if self.goods.count() == 0:
            return u'礼品'
        return ",".join([g.hs_type if g.hs_type else u'礼品' for g in self.goods.all()])

    def get_goods_content_bdt(self):
        return ",".join([g.brand + g.hs_type if g.hs_type else u'礼品' for g in self.goods.all()])

    def get_goods_content_lux(self):
        return ",".join([g.brand + " " + g.description for g in self.goods.all()])

    def get_declare_value_bdt(self):
        v = 0
        for g in self.goods.all():
            v += g.unit_price * g.quantity * Decimal(0.5)
        return v

    def get_usps_rec_add1(self):
        return remove_sheng_shi_zizhiqu((self.recv_province + self.recv_city + self.recv_area))

    def get_usps_cn_address(self):
        l = remove_sheng_shi_zizhiqu((self.recv_province + self.recv_city + self.recv_area))
        m = self.recv_address.replace(self.recv_province, '').replace(self.recv_city, '').replace(self.recv_area, '')
        c = l + m
        return c[0:20], c[20:], len(c)

    def get_eng_name(self):
        a = lazy_pinyin(self.recv_name)
        if len(a) > 1:
            return " ".join([a[0], "".join(a[1:])]).title()
        else:
            return "".join(a).title()

    def get_air_waybill(self):
        if self.pallet and self.pallet.air_waybill:
            return self.pallet.air_waybill
        else:
            return None

    def update_cn_tracking_info(self):
        if self.status.name == '国内派送':
            cn_status = self.status_set.filter(status=self.status).first()
            if cn_status.api_cnt <= 40:
                cn_status.update_cn_status()
        elif self.status.name == '海关查验':
            # fetch json
            cn_json = check_cn_status(self)
            if cn_json:
                # create 清关完毕, 国内派送

                finish_custom_entry = WaybillStatusEntry.objects.get(name='清关完毕')
                WaybillStatus.objects.create(waybill=self, status=finish_custom_entry)

                cn_status_entry = WaybillStatusEntry.objects.get(name='国内派送')
                cn_status = WaybillStatus.objects.create(waybill=self, status=cn_status_entry, cn_status_json=cn_json,
                                                         api_cnt=1)

                cn_status.update_waybill_status_with_cn_status(cn_json)

    def get_clean_address(self):
        addr = self.recv_address
        if self.recv_city in addr:
            addr = addr.replace(self.recv_city, '')
        if self.recv_area in addr:
            addr = addr.replace(self.recv_area, '')
        if self.recv_province in addr:
            addr = addr.replace(self.recv_province, '')
        return addr

    @classmethod
    def update_cn_sending_all(cls):
        qs = Waybill.objects.filter(status__name=u'国内派送')
        i = 0
        for w in qs:
            try:
                w.update_cn_tracking_info()
            except Exception as e:
                print w.tracking_no, e
            i += 1
            sys.stdout.write("\r%d/%d" % (i, qs.count()))
            sys.stdout.flush()

    def gen_bill(self):
        self.express_fee = self.get_express_fee()
        self.tax_fee = self.get_tax_fee()
        self.is_billed = True
        self.save()

    def get_fee(self):
        if self.weight < 1:
            return Decimal(8)
        else:
            return Decimal(8) + (self.weight - 1) * Decimal(6)

    def get_fee_actual(self):
        c = self.channel
        if self.weight < 1:
            return c.base_rate + self.package_fee
        else:
            return c.base_rate + (self.weight - Decimal('1')) * c.next_rate + self.package_fee

    def get_express_fee(self):
        c = self.channel
        if self.weight < 1:
            return c.base_rate
        else:
            return c.base_rate + (self.weight - Decimal('1')) * c.next_rate

    def get_tax_fee(self):
        rate = Currency.get_today_rate()

        if self.channel.tax and self.goods.all().count() > 0:
            return self.goods.aggregate(total=Sum(F('quantity') * F('unit_price'), output_field=models.DecimalField()))[
                       'total'] * Decimal('0.5') * Decimal("0.112") / rate
        else:
            return 0

    def get_tax_fee(self, rate):
        if self.channel.tax and self.goods.all().count() > 0:
            return self.goods.aggregate(total=Sum(F('quantity') * F('unit_price'), output_field=models.DecimalField()))[
                       'total'] * Decimal('0.5') * Decimal("0.112") / rate
        else:
            return 0

    def mark_error(self, user, goods_no, quantity):
        audit_status = WaybillStatusEntry.objects.get(name='已审核')
        succ = False
        msg = ''
        if self.status.name == u'运单异常':
            msg = u'订单已经是异常状态, 请勿重复标记'
        elif self.status.order_index > audit_status.order_index:
            msg = '状态为:%s, 无法标记异常' % self.status.name
        else:
            gs = self.goods.all()
            total_g = 0
            del_cnt = 0
            for g in gs:
                total_g += g.quantity
            for g in gs:
                if g.sku == goods_no:
                    if g.quantity >= quantity:
                        g.quantity -= quantity
                        if g.quantity == 0:
                            g.delete()
                        else:
                            g.save()
                        del_cnt += quantity
                        break
                    else:
                        quantity -= g.quantity
                        del_cnt += g.quantity
                        g.delete()

            if del_cnt == 0:
                msg = u'给定条码有误或个数有误'
                succ = False
            elif del_cnt == total_g:
                s = WaybillStatusEntry.objects.get(name='运单异常')
                WaybillStatus.objects.create(waybill=self, status=s, user=user, remark='用户问题单')
                msg = u'标记成功, 已将运单设置为异常状态'
                succ = True
            else:
                msg = u'已清除缺失商品'
                succ = True
        return msg, succ

    def update_yhc_status(self):
        if self.status.name == '国内清关':
            st = self.status_set.filter(status__name='国内清关').first()
            if st:
                yhc_json = get_yhc_status(self.tracking_no)
                if yhc_json:
                    st.cn_status_json = json.dumps(yhc_json['data'])
                    if yhc_json['data']['cn_transfer_no']:
                        self.cn_tracking = yhc_json['data']['cn_transfer_no']
                    if yhc_json['data']['express_status'] == '45':
                        finishState = WaybillStatusEntry.objects.get(name='已完成')
                        user = User.objects.get(username='yee')
                        WaybillStatus.objects.create(waybill=self, status=finishState, user=user)
                    st.save()
            self.save()

    def is_able_to_audit(self):
        audit_status = WaybillStatusEntry.objects.get(name='已审核')
        qty = self.get_goods_quantity()

        if not self.person_id and self.channel.name in CH_LIST_REQUIRED_PERSON_ID and self.src_loc.name != "NJ":
            return False, '运单缺少身份证, 无法审核'
        elif not self.cn_tracking and self.channel.name not in CH_LIST_NOT_REQUIRED_PERSON_ID:
            return False, '运单缺少国内单号, 无法审核'
        elif qty > 5:
            return False, "该单商品总数超过5个, 需要手动审核"
        elif self.status.order_index > audit_status.order_index:
            return False, "该订单状态为:" + self.status.name
        else:
            return True, ''

    def is_able_to_check_in(self):
        already_check_in = WaybillStatusEntry.objects.get(name='已入库')
        return self.status.order_index < already_check_in.order_index

    @classmethod
    def get_status_sum_up(cls, q):
        # <QuerySet [{'total': 1, 'status__name': '已审核'},...]
        if q:
            return cls.objects.filter(q).values('status__name').annotate(total=Count('status')).order_by(
                'status__order_index')
        return []

    def is_over_limit_per_batch(self):
        qs = Waybill.objects.filter(Q(status__name="打板中") | Q(status__name="已打板")).filter(channel=self.channel)
        same_name_cnt = qs.filter(recv_name=self.recv_name).count()
        same_person_id_cnt = qs.filter(person_id=self.person_id).count()
        if same_name_cnt >= 5 or same_person_id_cnt >= 5:
            return True
        return False

    def is_k_over_limit_per_batch(self):
        if self.channel.name in [CH18, CH17, CH19]:  # K1
            cnt = Waybill.objects.filter(Q(status__name="打板中") | Q(status__name="已打板")).filter(
                channel=self.channel).filter(person_id=self.person_id).count()
            return cnt >= 1
        return False

    def is_lux_brand_over_limit(self):
        is_lux = self.goods.filter(brand__iregex=r'(' + '|'.join(LUX_BRAND) + ')').count() > 0
        if is_lux:
            return Waybill.objects.filter(
                Q(status__name="打板中"),
                Q(goods__brand__iregex=r'(' + '|'.join(LUX_BRAND) + ')')).distinct().count() >= 15
        return False

    def is_required_person_id(self):
        return self.channel.name in CH_LIST_REQUIRED_PERSON_ID

    def is_lux_brand(self):
        return self.goods.filter(brand__iregex=r'(' + '|'.join(LUX_BRAND) + ')').count() > 0

    def special_channel_check(self):
        if self.channel.name in [CH14, CH8]:
            return self.goods.filter(description__iregex=r'(' + '|'.join(['鱼油', '眼药水']) + ')').count() > 0
        elif self.channel.name == CH12:
            return self.goods.filter(description__iregex=r'(' + '|'.join(['眼药水']) + ')').count() > 0
        else:
            return False

    @classmethod
    def query_filter(cls, channel_name, dt_end, dt_start, has_cn_tracking, has_person_id, in_no, loc, multi_search, qty,
                     search, src_loc, status_dt_end, status_dt_start, status_order_index):
        q = Q()
        if search:
            q.add((Q(pallet__pallet_no__istartswith=search) | Q(tracking_no__istartswith=search) |
                   Q(cn_tracking__istartswith=search) | Q(in_no__istartswith=search) |
                   Q(shelf_no__icontains=search) |
                   Q(pallet__air_waybill__air_waybill_no__istartswith=search) |
                   Q(goods__sku=search)), Q.AND)
        if in_no:
            q.add(Q(in_no__iexact=in_no), Q.AND)
        if status_order_index:
            q.add(Q(status__order_index=status_order_index), Q.AND)
        if src_loc:
            q.add(Q(src_loc__name=src_loc), Q.AND)
        if channel_name:
            q.add(Q(channel__name=channel_name), Q.AND)
        if has_person_id:
            if has_person_id == u'1':
                q.add(Q(person_id__exact=''), Q.AND)
            elif has_person_id == u'2':
                q.add(~Q(person_id__exact=''), Q.AND)
        if has_cn_tracking:
            if has_cn_tracking == u'1':
                q.add(Q(cn_tracking=None), Q.AND)
            elif has_cn_tracking == u'2':
                q.add(~Q(cn_tracking=None), Q.AND)
        if dt_start:
            q.add(Q(create_dt__gte=toTZDatetime(dt_start)), Q.AND)
        if dt_end:
            q.add(Q(create_dt__lt=toTZDatetime(dt_end)), Q.AND)
        if status_dt_start:
            q.add(Q(status_dt__gte=toTZDatetime(status_dt_start)), Q.AND)
        if status_dt_end:
            q.add(Q(status_dt__lt=toTZDatetime(status_dt_end)), Q.AND)
        if multi_search:
            tracking_list = [a.replace('\r', '').strip() for a in multi_search.split('\n') if
                             a.replace('\r', '').strip()]
            if len(tracking_list) > 0:
                q.add(Q(tracking_no__in=tracking_list) | Q(cn_tracking__in=tracking_list), Q.AND)
        if qty:
            q.add(Q(goods_num=qty), Q.AND)
        if loc:
            q.add(Q(init_loc=loc), Q.AND)

        qs = Waybill.objects.all()
        if status_dt_start or status_dt_end:
            qs = qs.annotate(status_dt=Max('status_set__create_dt'))
        if qty:
            qs = qs.annotate(goods_num=Sum('goods__quantity'))
        return qs.filter(q).distinct()


class WaybillStatusEntry(models.Model):
    # 排序
    order_index = models.PositiveSmallIntegerField()

    # 状态显示的描述
    name = models.CharField(max_length=400, blank=False, null=False)

    description = models.CharField(max_length=500, blank=True, null=True, default='')

    def __unicode__(self):
        return smart_unicode(self.name)


class SrcLoc(models.Model):
    name = models.CharField(max_length=30, blank=False)

    def __unicode__(self):
        return smart_unicode(self.name)


class Location(models.Model):
    #
    name = models.CharField(max_length=30, blank=False)

    #
    short_name = models.CharField(max_length=10, blank=True, default='')

    #
    address = models.CharField(max_length=150, blank=True, default='')

    #
    is_us_node = models.BooleanField(default=False)

    def __unicode__(self):
        return smart_unicode(self.name)


class WaybillStatus(models.Model):
    # 对应运单
    waybill = models.ForeignKey('Waybill', related_name='status_set', on_delete=models.CASCADE)

    # 对应状态
    status = models.ForeignKey('WaybillStatusEntry', related_name='status_set', on_delete=models.CASCADE)

    #
    location = models.ForeignKey('Location', related_name='status_set', on_delete=models.PROTECT, null=True, blank=True)

    # 该状态显示给用户的时间戳
    create_dt = models.DateTimeField(default=timezone.now, blank=False)

    #
    user = models.ForeignKey('auth.User', related_name='status_set', on_delete=models.PROTECT, null=True, blank=True)

    #
    remark = models.CharField(max_length=150, null=True, blank=True)

    #
    cn_status_json = models.CharField(max_length=10000, null=True, blank=True, default=None)

    #
    last_update = models.DateTimeField(auto_now=True)

    #
    api_cnt = models.IntegerField(verbose_name='api查询次数', default=0, null=True, blank=True)

    def __unicode__(self):
        return smart_unicode(self.status.name + ("," + self.remark if self.remark else ""))

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if self.id is None and self.waybill and self.status:
            self.waybill.status = self.status
            self.waybill.save()

        super(WaybillStatus, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                        update_fields=update_fields)

    def delete(self, using=None, keep_parents=False):
        waybill = self.waybill
        super(WaybillStatus, self).delete(using=using, keep_parents=keep_parents)
        waybill.status = waybill.status_set.all().order_by('-id').first().status
        waybill.save()

    @classmethod
    def get_most_recent_set(cls, user):
        return cls.objects.annotate(max_id=Max('waybill__status_set__id')).filter(id=F('max_id')).filter(user=user)

    def get_pallet_waybill_format(self):
        tracking_no = self.waybill.cn_tracking if self.waybill.cn_tracking else self.waybill.tracking_no
        id = self.waybill.id
        return {"tracking_no": tracking_no, "id": id, "channel_id": self.waybill.channel.id,
                "channel_name": self.waybill.channel.name, 'weight': self.waybill.weight}

    def get_cn_status_list(self):
        if self.status.name == "国内派送" and self.cn_status_json:
            cn_json = json.loads(self.cn_status_json)
            return sorted(
                [{'status__name': x.get('context', ''),
                  'create_dt': pytz.timezone('Asia/Shanghai').localize(parse_datetime(x.get('time', None)),
                                                                       is_dst=None)} for x in cn_json['data']],
                key=lambda x: x['create_dt'])
        else:
            return []

    def update_cn_status(self):
        if self.cn_status_json:
            cn_json = json.loads(self.cn_status_json)
            if cn_json['status'] < 4:

                new_status = check_cn_status(self.waybill)
                if new_status:
                    self.cn_status_json = new_status
                    self.update_waybill_status_with_cn_status(new_status)
                self.api_cnt += 1

        else:
            new_status = check_cn_status(self.waybill)
            if new_status:
                self.cn_status_json = new_status
                self.update_waybill_status_with_cn_status(new_status)
            self.api_cnt += 1
        self.save()

    def update_waybill_status_with_cn_status(self, new_status):
        new_cn_json = json.loads(new_status)
        if new_cn_json['status'] == 4 or self.special_check(new_cn_json):
            finish_status = WaybillStatusEntry.objects.get(name='已完成')
            WaybillStatus.objects.create(waybill=self.waybill, status=finish_status, user=self.user)
        elif new_cn_json['status'] > 4:
            exception_status = WaybillStatusEntry.objects.get(name='国内段异常')
            WaybillStatus.objects.create(waybill=self.waybill, status=exception_status, user=self.user,
                                         remark=CN_WAYBILL_STATUS[new_cn_json['status']])

    def get_cn_tracking_info(self):
        if self.status.name == "国内派送":
            # if self.last_update.date() < timezone.now().date():
            # 如果当前时间比最后一次更新的时间新,且订单状态未完成, 则调用API更新
            # self.update_cn_status()
            if self.cn_status_json:
                cn_json = json.loads(self.cn_status_json)
                return " {company}: {tracking}".format(company=cn_json.get('expTextName', ''),
                                                       tracking=cn_json.get('mailNo'))
            else:
                return u' 单号:{0}'.format(self.waybill.cn_tracking)
        else:
            return ""

    def special_check(self, new_cn_json):
        for obj in new_cn_json['data']:
            if u'已妥投' in obj['context']:
                return True
            elif u'已签收' in obj['context']:
                return True
        return False


class Good(models.Model):
    # 大类别
    cat1 = models.CharField(max_length=25, verbose_name=u'大类别', default='', blank=True)

    # 小类别
    cat2 = models.CharField(max_length=25, verbose_name=u'小类别', default='', blank=True)

    # 商品品牌
    brand = models.CharField(max_length=100, verbose_name=u'品牌')

    # 描述
    description = models.CharField(max_length=300, verbose_name=u'描述', default='', blank=True)

    # 对应运单
    waybill = models.ForeignKey('Waybill', related_name='goods', on_delete=models.CASCADE)

    # 个数
    quantity = models.PositiveSmallIntegerField(default=1, verbose_name=u'个数')

    # 单价 美金
    unit_price = models.DecimalField(max_digits=9, decimal_places=2, default=5, verbose_name=u'单价')

    # 单个重量 磅
    unit_weight = models.DecimalField(max_digits=5, decimal_places=2, default=2, verbose_name=u'单位磅重')

    # 备注
    remark = models.CharField(max_length=150, null=True, blank=True, verbose_name=u'备注')

    # 英文名
    english_name = models.CharField(max_length=100, blank=True, verbose_name=u'英文名', default='')

    # 规格型号
    spec = models.CharField(max_length=100, blank=True, verbose_name=u'规格信号', default='')

    # 单位
    unit = models.CharField(max_length=10, blank=True, verbose_name=u'单位', default=u'个')

    #
    sku = models.CharField(max_length=80, blank=True, verbose_name=u'条码', default='')

    # 海关类别
    hs_type = models.CharField(verbose_name=u'海关类别', default='', blank=True, max_length=30)

    # 海关类别编码
    hs_type_no = models.CharField(verbose_name=u'海关类别编码', default='', blank=True, max_length=20)

    # 图片URL
    img_url = models.CharField(verbose_name=u'图片URL', default='', blank=True, max_length=300)

    order_no = models.CharField(verbose_name=u'子订单号', default='', blank=True, max_length=100)

    shelf_no = models.CharField(verbose_name=u'货架号', default='', blank=True, max_length=30)

    def __unicode__(self):
        return "%s, %s %s" % (smart_unicode(self.cat2), smart_unicode(self.brand), smart_unicode(self.description))

    def get_usps_value(self):
        value = 40 + random.randint(0, 10) + random.random()
        return round(min(self.unit_price, value), 2)


class WaybillInvoice(models.Model):
    invoice_no = models.CharField(verbose_name=u'发票号码', max_length=20)

    waybill = models.ForeignKey('Waybill', verbose_name=u'运单', related_name='invoice', on_delete=models.PROTECT)

    depart_loc = models.CharField(verbose_name=u'起运地', max_length=20)

    arrival_loc = models.CharField(verbose_name=u'目的地', max_length=20)


class TaxItem(models.Model):
    tax_no = models.CharField(max_length=15, verbose_name=u'税号')

    name = models.CharField(max_length=50, verbose_name=u'品名及规格')

    unit = models.CharField(max_length=5, verbose_name=u'单位', blank=True, null=True)

    tax_price = models.DecimalField(max_digits=7, decimal_places=0, verbose_name=u'完税价格', blank=True, null=True)

    rate = models.DecimalField(verbose_name=u'税率', max_digits=3, decimal_places=2, blank=True, null=True)

    is_parrent = models.BooleanField(default=False, verbose_name=u'大类目')

    def __unicode__(self):
        return smart_unicode(self.name)


class QFTracking(models.Model):
    tracking_no = models.CharField(max_length=30, verbose_name=u'单号', unique=True)

    is_used = models.BooleanField(verbose_name=u'是否已用', default=False)

    waybill = models.ForeignKey('Waybill', verbose_name='运单', related_name='qf_tracking', null=True, default=None,
                                on_delete=models.SET_NULL)

    @classmethod
    def get_unused_trackings(cls, number=1):
        # set a bunch of tracking_no to be used
        trackings = []
        for o in cls.objects.filter(is_used=False).order_by("tracking_no")[:number]:
            o.is_used = True
            o.save()
            trackings.append(o.tracking_no)
        return trackings

    @classmethod
    def revert_tracking(cls, tracking):
        if cls.objects.filter(tracking_no=tracking).exists():
            t = cls.objects.get(tracking_no=tracking)
            t.is_used = False
            t.save()

    def __str__(self):
        return self.tracking_no


class CnTrackingCreateLog(models.Model):
    us_tracking = models.CharField(max_length=100, verbose_name=u'国际单号')
    cn_tracking = models.CharField(max_length=100, verbose_name=u'国内单号', blank=True, null=True)
    msg = models.CharField(max_length=200, verbose_name=u'结果信息', blank=True)
    status = models.CharField(max_length=10, verbose_name=u'状态码', blank=True)
    other = models.CharField(max_length=100, verbose_name=u'其他信息', blank=True, null=True)
    channel = models.ForeignKey('pallets.Channel', related_name='cn_tracking_create_logs', on_delete=models.SET_NULL,
                                verbose_name=u'渠道', null=True)
    create_dt = models.DateTimeField(auto_now_add=True, verbose_name=u'生成时间')


class ExceptionRecord(models.Model):
    waybill = models.OneToOneField('Waybill', related_name='exception_record', verbose_name=u'运单', null=True,
                                   on_delete=models.SET_NULL)

    user = models.ForeignKey('auth.User', related_name='exception_records', verbose_name=u'提交人', null=True,
                             on_delete=models.SET_NULL)

    create_dt = models.DateTimeField(auto_now_add=True, verbose_name=u'生成时间')

    remark = models.CharField(max_length=500, verbose_name='备注', null=True, blank=True, default='')

    area = models.CharField(max_length=100, verbose_name='区域', null=True, blank=True, default='')

    value = models.DecimalField(max_digits=9, decimal_places=2, default=0, verbose_name=u'价值')

    qty = models.PositiveSmallIntegerField(default=1, verbose_name=u'个数')

    description = models.CharField(max_length=100, verbose_name='物品名', null=True, blank=True, default='')

    type = models.CharField(max_length=50, verbose_name='类别', null=True, blank=True, default='')


class ExceptionRecordImage(models.Model):
    record = models.ForeignKey('ExceptionRecord', related_name='images', verbose_name=u'问题记录', on_delete=models.CASCADE)

    image = models.ImageField(null=True, blank=True, verbose_name=u'图片', upload_to='exception_records/%Y/%m',
                              max_length=100)


class Currency(models.Model):
    rate = models.DecimalField(max_digits=6, decimal_places=5, verbose_name=u'汇率')

    create_dt = models.DateField(auto_now_add=True, verbose_name=u'汇率日期')

    def __str__(self):
        return '%f, %s' % (self.rate, self.create_dt.strftime('%m-%d-%Y'))

    @classmethod
    def get_today_rate(cls):
        qs = Currency.objects.filter(create_dt=timezone.now().date())
        if qs.count() > 0:
            return qs.first().rate
        else:
            r = fetch_usd_cnh()
            Currency.objects.create(rate=r)
            return r
