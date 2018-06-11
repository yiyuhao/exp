# -*- coding: utf-8 -*
from __future__ import unicode_literals

from django.db import models
from django.db.models import Q
from django.utils.encoding import smart_unicode


class People(models.Model):
    name = models.CharField(max_length=30)

    id_no = models.CharField(max_length=30)

    mobile = models.CharField(max_length=30)

    id_card_backside = models.ImageField(verbose_name='身份证反面图片', null=True, blank=True, upload_to='id_card_back/%Y/%m',
                                         max_length=100)

    id_card_front = models.ImageField(verbose_name='身份证正面图片', null=True, blank=True, upload_to='id_card_front/%Y/%m',
                                      max_length=100)

    id_card = models.ImageField(verbose_name='身份证影印件(正反面在一张图片)', null=True, blank=True, upload_to='id_card/%Y/%m',
                                max_length=100)

    status = models.IntegerField(choices=((1, u'待审核'), (2, u'审核通过'), (3, u'审核不通过')),
                                 default=1, verbose_name=u'身份证审核状态')

    def __unicode__(self):
        return smart_unicode(self.name)

    def __str__(self):
        return self.name, self.id_no


# Create your models here.
class Address(models.Model):
    # 收件人
    name = models.CharField(max_length=30)

    # 省份
    province = models.CharField(max_length=20)

    # 市
    city = models.CharField(max_length=20)

    # 区县
    area = models.CharField(max_length=30)

    # 地址
    address = models.CharField(max_length=200)

    # 邮编
    zipcode = models.CharField(max_length=30)

    # 手机
    mobile = models.CharField(max_length=30)

    # 座机
    phone = models.CharField(max_length=30, blank=True, null=True)

    #
    people = models.ForeignKey('People', null=True, on_delete=models.SET_NULL)


class ExpressMark(models.Model):
    # 省份
    province = models.CharField(max_length=20)

    # 市
    city = models.CharField(max_length=20, blank=True, null=True, default='')

    # 区县
    area = models.CharField(max_length=30, blank=True, null=True, default='')

    # ems mark
    ems_mark1 = models.CharField(max_length=30)

    @classmethod
    def get_ems_mark1(cls, prov, city, area):
        prov = cls.process_prov(prov)
        city = cls.process_city(city)
        result = ""
        if ExpressMark.objects.filter(province__istartswith=prov).filter(city__istartswith=city).filter(
                area__istartswith=area).exists():
            result = ExpressMark.objects.filter(province__istartswith=prov).filter(city__istartswith=city).filter(
                area__istartswith=area).first().ems_mark1
        elif ExpressMark.objects.filter(province__istartswith=prov).filter(city__istartswith=city).exists():
            result = ExpressMark.objects.filter(province__istartswith=prov).filter(
                city__istartswith=city).first().ems_mark1
        elif ExpressMark.objects.filter(province__istartswith=prov).exists():
            result = ExpressMark.objects.filter(province__istartswith=prov).first().ems_mark1
        return result

    @classmethod
    def get_ems_k2(cls, prov, city, area):
        prov = cls.process_prov_k2(prov)
        city = cls.process_city(city)
        result = ""
        if ExpressMark.objects.filter(province__istartswith=prov).filter(
                        Q(city__istartswith=city) | Q(city__istartswith=area)).exists():
            result = ExpressMark.objects.filter(province__istartswith=prov).filter(
                Q(city__istartswith=city) | Q(city__istartswith=area)).first().ems_mark1
        elif ExpressMark.objects.filter(province__istartswith=prov).exists():
            result = ExpressMark.objects.filter(province__istartswith=prov).first().ems_mark1
        return result

    @classmethod
    def process_prov(cls, prov):
        return prov.replace('省', '').replace('市', '')

    @classmethod
    def process_prov_k2(cls, prov):
        s = ['新疆', '广西', '西藏', '宁夏', '内蒙古']

        for x in s:
            if x in prov:
                return x

        return prov.replace('省', '').replace('市', '')

    @classmethod
    def process_city(cls, city):
        return city.replace('市', '')
