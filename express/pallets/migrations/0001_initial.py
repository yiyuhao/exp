# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-30 00:10
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Pallet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch_no', models.CharField(blank=True, max_length=50, null=True)),
                ('weight', models.DecimalField(decimal_places=2, max_digits=5)),
                ('create_dt', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('create_user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='pallets', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
