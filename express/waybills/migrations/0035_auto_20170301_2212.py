# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-01 22:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waybills', '0034_auto_20170228_2244'),
    ]

    operations = [
        migrations.AlterField(
            model_name='waybill',
            name='transaction_no',
            field=models.CharField(default=b'<function uuid4 at 0x109e3f488>', editable=False, max_length=40, unique=True, verbose_name='\u4ea4\u6613\u53f7'),
        ),
    ]
