# -*- coding: utf-8 -*
from __future__ import unicode_literals

from django.db import models

# Create your models here.
from django.db.models import Q, Sum
from django.utils import timezone
from django.utils.encoding import smart_unicode

TIMESTAMP_LEN = 6
SERIAL_NO_LEN = 3
AIRWAYBILL_STATUS = (
    (1, '已生成'),
    (2, '已出库'),
    (3, '国内派送'),
)

CH1 = 'Y1'  # 电商
CH2 = 'U'  # 邮政
CH3 = 'T1'  # 一号仓
CH4 = 'T2'  # 八达通
CH5 = 'T3'  # 华美
CH6 = 'Y2'  # 青岛电商
CH7 = 'Y3'  # 福建
CH8 = 'A'  # 杭州
CH9 = 'B'  # 天津
CH10 = 'C'  # 厦门
CH11 = 'D'  # 广西
CH12 = 'E'  # 北京
CH13 = 'F'  # 郑州
CH14 = 'A1'  # 杭州 新面单
CH15 = 'Z1'  # 致一 电商
CH16 = 'H'  # HXQ
CH17 = 'K'  # 晋江
CH18 = 'K1'  # 晋江 新面单
CH19 = 'K2'  # 晋江2 新面单
CH20 = 'Q'  # 青岛包税

CH_LIST_REQUIRED_PERSON_ID = [CH1, CH6, CH7, CH8, CH9, CH10, CH11, CH12, CH13, CH14, CH17, CH18, CH19, CH20]
CH_LIST_NOT_REQUIRED_PERSON_ID = [CH2, CH3, CH4, CH5, CH15, CH16]


class Airline(models.Model):
    # 航空公司名称
    name = models.CharField(max_length=30, verbose_name=u'航空公司名称')

    # 代码
    code = models.CharField(max_length=10, verbose_name=u'航空公司代码')

    #
    info = models.CharField(verbose_name=u'航空公司信息', max_length=150)

    def __unicode__(self):
        return smart_unicode(self.name)


class Receiver(models.Model):
    # 名称
    name = models.CharField(verbose_name=u'收件公司名', max_length=100)

    # 收件公司信息
    info = models.CharField(verbose_name=u'收件公司信息', max_length=150)

    def __unicode__(self):
        return smart_unicode(self.name)


class Carrier(models.Model):
    # 名称
    name = models.CharField(verbose_name=u'货代名', max_length=100)

    # 收件公司信息
    info = models.CharField(verbose_name=u'货代公司信息', max_length=150)

    # IATA代码
    iata = models.CharField(verbose_name=u'货代IATA代码', max_length=10, blank=True)

    # 货运代理公司结算帐号
    account_no = models.CharField(verbose_name=u'货代结算账号', max_length=10, blank=True)

    def __unicode__(self):
        return smart_unicode(self.name)


class AirWaybill(models.Model):
    # 航空提单号
    air_waybill_no = models.CharField(unique=True, max_length=30, blank=True, default='', verbose_name=u'航空提单号')

    # 渠道
    channel = models.ForeignKey('Channel', on_delete=models.SET_NULL, related_name='air_waybills', default=None,
                                null=True, blank=True, verbose_name=u'渠道')
    # 航班号
    flight_no = models.CharField(max_length=10, blank=True, default='', verbose_name=u'航班号', null=True)

    # 创建人
    user = models.ForeignKey('auth.User', related_name='air_waybills', on_delete=models.PROTECT, verbose_name=u'创建人')

    # 航空公司
    airline = models.ForeignKey('Airline', related_name='air_waybills', on_delete=models.PROTECT, verbose_name=u'航空公司',
                                null=True, blank=True)

    # 始发港代码
    depart_code = models.CharField(max_length=10, verbose_name=u'始发港代码', null=True, blank=True)

    # 目的地代码
    arrival_code = models.CharField(max_length=10, verbose_name=u'目的地代码', null=True, blank=True)

    # 航班出发日期
    depart_date = models.DateTimeField(verbose_name=u'航班出发日期', null=True, blank=True)

    # 航班到达日期
    arrival_date = models.DateTimeField(verbose_name=u'航班到达日期', null=True, blank=True)

    # 处理信息 27
    handling_info = models.CharField(verbose_name=u'处理信息', max_length=150, null=True, blank=True)

    # 发件公司信息
    sender_info = models.CharField(verbose_name=u'发件公司信息', max_length=150, null=True, blank=True)

    # 收件公司信息
    receiver = models.ForeignKey('Receiver', related_name='air_waybills', on_delete=models.PROTECT,
                                 verbose_name=u'收件公司', null=True, blank=True)

    # 货代公司信息
    carrier = models.ForeignKey('Carrier', related_name='air_waybills', on_delete=models.PROTECT, verbose_name=u'货代公司',
                                null=True, blank=True)

    # 创建时间
    create_dt = models.DateTimeField(auto_now_add=True)

    # 最后修改时间
    last_modified = models.DateTimeField(auto_now=True)

    #
    is_send_out = models.BooleanField(verbose_name="是否出库", default=False)

    #
    status = models.IntegerField(verbose_name="状态", default=1)

    def __unicode__(self):
        return smart_unicode(self.air_waybill_no)

    @classmethod
    def get_next_auto_air_waybill(cls, employee, air_waybill_no, channel_id):
        if air_waybill_no == '':
            air_waybill_no = cls.get_next_air_waybill_no(employee)
        channel = None
        if channel_id:
            try:
                channel = Channel.objects.filter(id=int(channel_id)).first()
            except:
                pass
        return cls.objects.create(user=employee.user, air_waybill_no=air_waybill_no, channel=channel)

    @classmethod
    def get_next_air_waybill_no(cls, employee):
        short_name = "A" + employee.loc.short_name

        curr_timestamp = timezone.now().strftime("%Y%m%d")[2:]
        next_serial_no = 1
        pre_fix_len = len(short_name)
        if cls.objects.filter(air_waybill_no__istartswith=short_name).order_by('-id').exists():
            last = cls.objects.filter(air_waybill_no__istartswith=short_name).order_by('-id')[0]
            timestamp = last.air_waybill_no[pre_fix_len: pre_fix_len + TIMESTAMP_LEN]
            serial_no = int(last.air_waybill_no[pre_fix_len + TIMESTAMP_LEN:])
            next_serial_no = serial_no + 1
            if timestamp != curr_timestamp:
                next_serial_no = 1
        return '%s%s%03d' % (short_name, curr_timestamp, next_serial_no)

    def get_waybills_count(self):
        cnt = 0
        for pallet in self.pallets.all():
            cnt += pallet.waybills.all().count()
        return cnt

    get_waybills_count.short_description = '运单数'

    def get_status(self):
        if self.status == 1:
            return "已生成"
        elif self.status == 2:
            return "已出库"
        else:
            return "国内派送"

    get_status.short_description = '状态'

    def get_pallets_count(self):
        return self.pallets.count()

    get_pallets_count.short_description = '托盘数'

    def get_weight(self):
        ps = Pallet.objects.filter(air_waybill=self).aggregate(weight=Sum('weight'))
        return ps['weight']

    get_weight.short_description = '重量'

    def get_finish_waybills_count(self):
        cnt = 0
        for pallet in self.pallets.all():
            cnt += pallet.waybills.filter(status__name=u'已完成').count()
        return cnt

    get_finish_waybills_count.short_description = '已完成包裹'

    def get_not_finish_waybills_count(self):
        cnt = 0
        for pallet in self.pallets.all():
            cnt += pallet.waybills.filter(~Q(status__name=u'已完成')).count()
        return cnt

    get_not_finish_waybills_count.short_description = '未完成包裹'


class Channel(models.Model):
    name = models.CharField(max_length=100, verbose_name=u'渠道名')

    loc = models.CharField(max_length=100, verbose_name=u'地点', blank=True, null=True, default='')

    base_rate = models.DecimalField(verbose_name=u'首磅', decimal_places=2, max_digits=5, default=0, blank=True)

    next_rate = models.DecimalField(verbose_name=u'续磅', decimal_places=2, max_digits=5, default=0, blank=True)

    tax = models.BooleanField(verbose_name=u'是否征税', default=False)

    def __unicode__(self):
        return smart_unicode(self.name)


class Pallet(models.Model):
    #
    pallet_no = models.CharField(unique=True, max_length=50, blank=True, null=True)

    #
    weight = models.DecimalField(max_digits=10, decimal_places=2)

    #
    user = models.ForeignKey('auth.User', related_name='pallets', on_delete=models.PROTECT)

    #
    air_waybill = models.ForeignKey('AirWaybill', related_name='pallets', on_delete=models.SET_NULL, null=True,
                                    blank=True)

    # 创建时间
    create_dt = models.DateTimeField(auto_now_add=True)

    # 最后修改时间
    last_modified = models.DateTimeField(auto_now=True)

    # 备注
    remark = models.CharField(max_length=100, blank=True, default='')

    # 渠道
    channel = models.ForeignKey('Channel', related_name='pallets', on_delete=models.SET_NULL, null=True, blank=True)

    #
    # is_send_out = models.BooleanField(verbose_name="是否已经出库", default=False)

    def __str__(self):
        return self.pallet_no

    @classmethod
    def get_next_pallet_no(cls, shortname):
        short_name = "M" + shortname
        curr_timestamp = timezone.now().strftime("%Y%m%d")[2:]
        next_serial_no = 1
        pre_fix_len = len(short_name)
        if cls.objects.filter(pallet_no__istartswith=short_name).order_by('-pallet_no').exists():
            last = cls.objects.filter(pallet_no__istartswith=short_name).order_by('-pallet_no')[0]
            timestamp = last.pallet_no[pre_fix_len: pre_fix_len + TIMESTAMP_LEN]
            serial_no = int(last.pallet_no[pre_fix_len + TIMESTAMP_LEN:])
            next_serial_no = serial_no + 1
            if timestamp != curr_timestamp:
                next_serial_no = 1
        return '%s%s%03d' % (short_name, curr_timestamp, next_serial_no)

    def get_status(self):
        if self.air_waybill is None:
            return '已生成'
        elif self.air_waybill and self.air_waybill.status == 1:
            return '已建提单'
        else:
            return '已出库'

    get_status.short_description = '状态'

    def get_waybills_count(self):
        return self.waybills.count()

    get_waybills_count.short_description = '运单数'

    def get_weight(self):
        total = 0
        for w in self.waybills.all():
            total += w.weight
        return total
