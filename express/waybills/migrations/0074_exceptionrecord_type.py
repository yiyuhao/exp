# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-05-02 22:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('waybills', '0073_exceptionrecord_exceptionrecordimage'),
    ]

    operations = [
        migrations.AddField(
            model_name='exceptionrecord',
            name='type',
            field=models.CharField(blank=True, default='', max_length=50, null=True, verbose_name='\u7c7b\u522b'),
        ),
    ]
