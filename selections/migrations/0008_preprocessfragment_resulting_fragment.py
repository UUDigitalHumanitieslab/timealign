# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-10-14 20:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0026_auto_20181003_0851'),
        ('selections', '0007_selection_other_label'),
    ]

    operations = [
        migrations.AddField(
            model_name='preprocessfragment',
            name='resulting_fragment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fragment_preprocess', to='annotations.Fragment'),
        ),
    ]