# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-04 21:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('waybills', '0049_qftracking_waybill'),
    ]

    operations = [
        migrations.AddField(
            model_name='good',
            name='img_url',
            field=models.CharField(blank=True, default='', max_length=300, verbose_name='\u56fe\u7247URL'),
        ),
        migrations.AlterField(
            model_name='qftracking',
            name='waybill',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qf_tracking', to='waybills.Waybill', verbose_name='\u8fd0\u5355'),
        ),
    ]
