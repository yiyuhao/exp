# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-01 05:57
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0006_auto_20170201_0051'),
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loc', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.Loc', verbose_name='Working location')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterField(
            model_name='customer',
            name='repr_name',
            field=models.CharField(blank=True, max_length=30, verbose_name='Sender name on waybill'),
        ),
    ]
