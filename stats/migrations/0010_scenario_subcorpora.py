# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-11-23 12:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0027_auto_20181123_1228'),
        ('stats', '0009_auto_20180620_1232'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='subcorpora',
            field=models.ManyToManyField(blank=True, to='annotations.SubCorpus'),
        ),
    ]