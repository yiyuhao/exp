# -*- coding: utf-8 -*

from __future__ import unicode_literals
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import smart_unicode
from ckeditor.fields import RichTextField


class Category(models.Model):
    name = models.CharField(max_length=20, verbose_name=u'分类名')

    def __unicode__(self):
        return smart_unicode(self.name)


class Post(models.Model):
    category = models.ForeignKey('Category', on_delete=models.PROTECT, related_name='posts', verbose_name=u'分类')

    title = models.CharField(max_length=100, verbose_name=u'标题')

    content = RichTextField(verbose_name=u'内容')

    user = models.ForeignKey('auth.User', related_name='posts', on_delete=models.PROTECT, verbose_name=u'作者')

    create_dt = models.DateField(null=True, default=timezone.now, verbose_name=u'创建时间')

    last_modified = models.DateTimeField(auto_now=True)

    is_del = models.BooleanField(default=False, verbose_name='删除')

    def __unicode__(self):
        return smart_unicode(self.title)

    def get_url(self):
        return reverse("blog-detail", kwargs={"pk": self.id})
