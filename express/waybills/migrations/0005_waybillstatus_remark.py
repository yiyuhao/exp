# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-31 05:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waybills', '0004_auto_20170131_0038'),
    ]

    operations = [
        migrations.AddField(
            model_name='waybillstatus',
            name='remark',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
    ]
