# -*- coding: utf-8 -*
from __future__ import unicode_literals
from django.db import models


class Order(models.Model):
    name = models.CharField(verbose_name="姓名", max_length=20)

    person_id = models.CharField(verbose_name="身份证号", max_length=18, blank=True, null=True, default='')

    province = models.CharField(verbose_name="省份", max_length=20)

    city = models.CharField(verbose_name="市", max_length=20)

    mobile = models.CharField(verbose_name="手机", max_length=11)

    order_no = models.CharField(verbose_name="订单号", max_length=50)

    is_sent = models.BooleanField(verbose_name='是否已通知顾客', default=False)
