# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-10 11:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('addresses', '0003_auto_20180410_2047'),
    ]

    operations = [
        migrations.AddField(
            model_name='people',
            name='id_card',
            field=models.ImageField(blank=True, null=True, upload_to='id_card/%Y/%m', verbose_name='\u8eab\u4efd\u8bc1\u5f71\u5370\u4ef6(\u6b63\u53cd\u9762\u5728\u4e00\u5f20\u56fe\u7247)'),
        ),
        migrations.AddField(
            model_name='people',
            name='status',
            field=models.IntegerField(choices=[(1, '\u5f85\u5ba1\u6838'), (2, '\u5ba1\u6838\u901a\u8fc7'), (3, '\u5ba1\u6838\u4e0d\u901a\u8fc7')], default=1, verbose_name='\u8eab\u4efd\u8bc1\u5ba1\u6838\u72b6\u6001'),
        ),
    ]
