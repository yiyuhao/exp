# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-11 21:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, verbose_name='\u59d3\u540d')),
                ('person_id', models.CharField(blank=True, default='', max_length=18, null=True, verbose_name='\u8eab\u4efd\u8bc1\u53f7')),
                ('province', models.CharField(max_length=20, verbose_name='\u7701\u4efd')),
                ('city', models.CharField(max_length=20, verbose_name='\u5e02')),
                ('mobile', models.CharField(max_length=11, verbose_name='\u624b\u673a')),
                ('order_no', models.CharField(max_length=50, verbose_name='\u8ba2\u5355\u53f7')),
            ],
        ),
    ]
