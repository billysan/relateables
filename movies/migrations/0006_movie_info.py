# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-08 16:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0005_auto_20170408_1008'),
    ]

    operations = [
        migrations.AddField(
            model_name='movie',
            name='info',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
    ]
