# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-25 05:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waybills', '0027_waybill_transaction_no'),
    ]

    operations = [
        migrations.AlterField(
            model_name='waybill',
            name='transaction_no',
            field=models.CharField(editable=False, max_length=40, null=True, unique=True, verbose_name='\u4ea4\u6613\u53f7'),
        ),
    ]
