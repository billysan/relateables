# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-08 07:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0003_auto_20170408_0945'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movie',
            name='is_explored',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='movie',
            name='rating',
            field=models.IntegerField(default=0),
        ),
    ]
