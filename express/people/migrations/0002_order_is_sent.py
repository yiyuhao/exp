# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-11 23:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='is_sent',
            field=models.BooleanField(default=False, verbose_name='\u662f\u5426\u5df2\u901a\u77e5\u987e\u5ba2'),
        ),
    ]
