# -*- coding: utf-8 -*
from __future__ import unicode_literals

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# Create your models here.

#
# class Log(models.Model):
#     #
#     content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
#
#     #
#     object_id = models.PositiveIntegerField()
#
#     #
#     content_object = GenericForeignKey('content_type', 'object_id')
#
#     #
#     change_message = models.TextField(blank=True)
#
#
#     #
#     remark = models.CharField(max_length=150, null=True, blank=True)
#
#     #
#     create_user = models.ForeignKey('auth.User', related_name='waybills', on_delete=models.PROTECT,
#     null=True)
#     #
#     #创建时间
#     create_dt = models.DateTimeField(auto_now_add=True)
#
#     #最后修改时间
#     last_modified = models.DateTimeField(auto_now=True)
