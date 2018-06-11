# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-04 09:22
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_auto_20170203_1923'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='address',
            field=models.CharField(blank=True, max_length=100, verbose_name='\u53d1\u4ef6\u4eba\u5730\u5740'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='mobile',
            field=models.CharField(max_length=30, validators=[django.core.validators.RegexValidator('^([0-9]+)$', message='\u8bf7\u8f93\u5165\u4ec5\u5305\u542b\u6570\u5b57\u7684\u6709\u6548\u7535\u8bdd\u53f7\u7801')], verbose_name='\u53d1\u4ef6\u4eba\u7535\u8bdd'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='repr_name',
            field=models.CharField(blank=True, max_length=30, verbose_name='\u53d1\u4ef6\u4eba\u59d3\u540d'),
        ),
    ]
