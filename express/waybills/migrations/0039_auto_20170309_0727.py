# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-09 07:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waybills', '0038_auto_20170309_0726'),
    ]

    operations = [
        migrations.AlterField(
            model_name='waybill',
            name='recv_city',
            field=models.CharField(max_length=20, verbose_name='\u5e02'),
        ),
    ]
