# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-25 04:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pallets', '0007_auto_20170224_0227'),
    ]

    operations = [
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='\u6e20\u9053\u540d')),
            ],
        ),
    ]
