# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime

from django.db import models


class Banner(models.Model):
    title = models.CharField(max_length=100, null=True, blank=True, verbose_name=u'轮播图上的第一行大字')
    title2 = models.CharField(max_length=100, null=True, blank=True, verbose_name=u'轮播图上的第二行大字')
    content = models.CharField(max_length=100, null=True, blank=True, verbose_name=u'轮播图上第一行小字')
    content2 = models.CharField(max_length=100, null=True, blank=True, verbose_name=u'轮播图上的第二行小字')
    image = models.ImageField(upload_to='banner/%Y/%m', verbose_name=u'轮播图', max_length=100)
    index = models.IntegerField(default=100, verbose_name=u'优先级(整数, 首页选优先级最小的3张展示)')
    add_time = models.DateTimeField(default=datetime.now, verbose_name=u'添加时间')

    class Meta:
        verbose_name = u'首页轮播图'
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.title

