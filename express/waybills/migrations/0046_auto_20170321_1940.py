# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-21 19:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('waybills', '0045_waybill_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='waybill',
            name='status',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='waybills', to='waybills.WaybillStatusEntry', verbose_name='\u72b6\u6001'),
        ),
    ]
