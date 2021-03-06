# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-04 00:29
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('waybills', '0007_auto_20170203_1923'),
    ]

    operations = [
        migrations.AddField(
            model_name='waybill',
            name='send_address',
            field=models.CharField(blank=True, max_length=100, verbose_name='\u53d1\u4ef6\u4eba\u5730\u5740'),
        ),
        migrations.AddField(
            model_name='waybill',
            name='send_mobile',
            field=models.CharField(blank=True, max_length=30, verbose_name='\u53d1\u4ef6\u4eba\u7535\u8bdd'),
        ),
        migrations.AddField(
            model_name='waybill',
            name='send_name',
            field=models.CharField(blank=True, max_length=30, verbose_name='\u53d1\u4ef6\u4eba'),
        ),
        migrations.AlterField(
            model_name='waybill',
            name='charge_rate',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True, verbose_name='\u8d39\u7387'),
        ),
        migrations.AlterField(
            model_name='waybill',
            name='create_dt',
            field=models.DateTimeField(auto_now_add=True, verbose_name='\u751f\u6210\u65f6\u95f4'),
        ),
        migrations.AlterField(
            model_name='waybill',
            name='is_self_define',
            field=models.BooleanField(default=True, verbose_name='\u662f\u5426\u81ea\u5b9a\u4e49\u5355\u53f7'),
        ),
        migrations.AlterField(
            model_name='waybill',
            name='last_modified',
            field=models.DateTimeField(auto_now=True, verbose_name='\u6700\u540e\u4fee\u6539'),
        ),
        migrations.AlterField(
            model_name='waybill',
            name='pallet',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='waybills', to='pallets.Pallet', verbose_name='\u6240\u5c5e\u6258\u76d8'),
        ),
        migrations.AlterField(
            model_name='waybill',
            name='recv_address',
            field=models.CharField(max_length=100, verbose_name='\u5730\u5740'),
        ),
        migrations.AlterField(
            model_name='waybill',
            name='recv_area',
            field=models.CharField(max_length=20, verbose_name='\u533a\u53bf'),
        ),
        migrations.AlterField(
            model_name='waybill',
            name='recv_city',
            field=models.CharField(max_length=10, verbose_name='\u5e02'),
        ),
        migrations.AlterField(
            model_name='waybill',
            name='recv_mobile',
            field=models.CharField(max_length=30, verbose_name='\u624b\u673a'),
        ),
        migrations.AlterField(
            model_name='waybill',
            name='recv_name',
            field=models.CharField(max_length=30, verbose_name='\u6536\u4ef6\u4eba'),
        ),
        migrations.AlterField(
            model_name='waybill',
            name='recv_phone',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='\u7535\u8bdd'),
        ),
        migrations.AlterField(
            model_name='waybill',
            name='recv_province',
            field=models.CharField(max_length=10, verbose_name='\u7701'),
        ),
        migrations.AlterField(
            model_name='waybill',
            name='recv_zipcode',
            field=models.CharField(max_length=15, verbose_name='\u90ae\u7f16'),
        ),
        migrations.AlterField(
            model_name='waybill',
            name='remark',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='\u5907\u6ce8'),
        ),
        migrations.AlterField(
            model_name='waybill',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='waybills', to=settings.AUTH_USER_MODEL, verbose_name='\u7528\u6237'),
        ),
        migrations.AlterField(
            model_name='waybill',
            name='weight',
            field=models.DecimalField(decimal_places=2, max_digits=5, verbose_name='\u5305\u88f9\u91cd\u91cf'),
        ),
    ]
