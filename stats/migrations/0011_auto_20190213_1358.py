# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-02-13 13:58
from __future__ import unicode_literals

from django.db import migrations
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0010_scenario_subcorpora'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scenario',
            name='mds_fragments',
            field=picklefield.fields.PickledObjectField(editable=False, null=True, verbose_name=b'MDS fragments'),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='mds_labels',
            field=picklefield.fields.PickledObjectField(editable=False, null=True, verbose_name=b'MDS labels'),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='mds_matrix',
            field=picklefield.fields.PickledObjectField(editable=False, null=True, verbose_name=b'MDS matrix'),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='mds_model',
            field=picklefield.fields.PickledObjectField(editable=False, null=True, verbose_name=b'MDS model'),
        ),
    ]
