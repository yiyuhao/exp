# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-14 21:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pallets', '0005_auto_20170214_2000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carrier',
            name='account_no',
            field=models.CharField(blank=True, max_length=10, verbose_name='\u8d27\u4ee3\u7ed3\u7b97\u8d26\u53f7'),
        ),
        migrations.AlterField(
            model_name='carrier',
            name='iata',
            field=models.CharField(blank=True, max_length=10, verbose_name='\u8d27\u4ee3IATA\u4ee3\u7801'),
        ),
    ]
