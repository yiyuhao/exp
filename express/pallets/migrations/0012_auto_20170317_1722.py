# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-17 17:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pallets', '0011_auto_20170306_1817'),
    ]

    operations = [
        migrations.AlterField(
            model_name='airwaybill',
            name='airline',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='air_waybills', to='pallets.Airline', verbose_name='\u822a\u7a7a\u516c\u53f8'),
        ),
        migrations.AlterField(
            model_name='airwaybill',
            name='arrival_code',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='\u76ee\u7684\u5730\u4ee3\u7801'),
        ),
        migrations.AlterField(
            model_name='airwaybill',
            name='arrival_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='\u822a\u73ed\u5230\u8fbe\u65e5\u671f'),
        ),
        migrations.AlterField(
            model_name='airwaybill',
            name='carrier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='air_waybills', to='pallets.Carrier', verbose_name='\u8d27\u4ee3\u516c\u53f8'),
        ),
        migrations.AlterField(
            model_name='airwaybill',
            name='depart_code',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='\u59cb\u53d1\u6e2f\u4ee3\u7801'),
        ),
        migrations.AlterField(
            model_name='airwaybill',
            name='depart_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='\u822a\u73ed\u51fa\u53d1\u65e5\u671f'),
        ),
        migrations.AlterField(
            model_name='airwaybill',
            name='flight_no',
            field=models.CharField(blank=True, default='', max_length=10, null=True, verbose_name='\u822a\u73ed\u53f7'),
        ),
        migrations.AlterField(
            model_name='airwaybill',
            name='handling_info',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='\u5904\u7406\u4fe1\u606f'),
        ),
        migrations.AlterField(
            model_name='airwaybill',
            name='receiver',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='air_waybills', to='pallets.Receiver', verbose_name='\u6536\u4ef6\u516c\u53f8'),
        ),
        migrations.AlterField(
            model_name='airwaybill',
            name='sender_info',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='\u53d1\u4ef6\u516c\u53f8\u4fe1\u606f'),
        ),
        migrations.AlterField(
            model_name='pallet',
            name='air_waybill',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pallets', to='pallets.AirWaybill'),
        ),
    ]
