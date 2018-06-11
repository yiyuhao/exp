# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-31 05:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('waybills', '0003_auto_20170131_0031'),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('address', models.CharField(blank=True, default='', max_length=150)),
            ],
        ),
        migrations.AddField(
            model_name='waybillstatus',
            name='location',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='status_set', to='waybills.Location'),
        ),
    ]
