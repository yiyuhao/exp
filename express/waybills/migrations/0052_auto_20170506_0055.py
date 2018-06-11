# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-05-06 04:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('waybills', '0051_auto_20170407_2131'),
    ]

    operations = [
        migrations.CreateModel(
            name='SrcLoc',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
            ],
        ),
        migrations.AddField(
            model_name='waybill',
            name='src_loc',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='waybills', to='waybills.SrcLoc', verbose_name='\u6765\u6e90\u5730'),
        ),
    ]
