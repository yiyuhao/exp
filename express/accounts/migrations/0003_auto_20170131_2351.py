# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-01 04:51
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20170131_2342'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='user_ptr',
        ),
        migrations.RemoveField(
            model_name='employee',
            name='customer_ptr',
        ),
        migrations.RemoveField(
            model_name='employee',
            name='loc',
        ),
        migrations.DeleteModel(
            name='Customer',
        ),
        migrations.DeleteModel(
            name='Employee',
        ),
    ]
