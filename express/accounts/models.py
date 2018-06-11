# -*- coding: utf-8 -*

from __future__ import unicode_literals
from django.utils.encoding import smart_unicode

from django.db import models

from django.contrib.auth.models import User

from django.core.validators import RegexValidator
# class Loc(models.Model):
#     class Meta:
#         verbose_name="Work Location"
#         verbose_name_plural = "Work Locations"
#
#     name = models.CharField(unique=True, max_length=30)
#
#     short_name = models.CharField(unique=True, max_length=10)
#
#     def __unicode__(self):
#         return smart_unicode(self.short_name)


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    mobile = models.CharField(verbose_name='发件人电话',max_length=30, validators=[RegexValidator(r'^([0-9]+)$', message="请输入仅包含数字的有效电话号码")])

    repr_name = models.CharField(verbose_name='发件人姓名', max_length=30, blank=True)

    address = models.CharField(verbose_name='发件人地址', max_length=100, blank=True)

    loc = models.ForeignKey('waybills.Location', verbose_name='最近的集运中心', default=1)

    def __unicode__(self):
        return smart_unicode(self.repr_name)


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    loc = models.ForeignKey('waybills.Location', verbose_name='工作位置')

    def __unicode__(self):
        return "%s | %s" % (self.user.get_full_name(), smart_unicode(self.loc.short_name))
