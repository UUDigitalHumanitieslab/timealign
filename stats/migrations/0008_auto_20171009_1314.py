# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0007_auto_20171004_1500'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='mds_fragments',
            field=picklefield.fields.PickledObjectField(verbose_name=b'MDS fragments', editable=False, blank=b'True'),
        ),
        migrations.AddField(
            model_name='scenario',
            name='mds_labels',
            field=picklefield.fields.PickledObjectField(verbose_name=b'MDS labels', editable=False, blank=b'True'),
        ),
        migrations.AddField(
            model_name='scenario',
            name='mds_matrix',
            field=picklefield.fields.PickledObjectField(verbose_name=b'MDS matrix', editable=False, blank=b'True'),
        ),
        migrations.AddField(
            model_name='scenario',
            name='mds_model',
            field=picklefield.fields.PickledObjectField(verbose_name=b'MDS model', editable=False, blank=b'True'),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='mds_dimensions',
            field=models.PositiveIntegerField(help_text=b'Number of dimensions to use in Multidimensional Scaling. Should be between 2 and 5.', verbose_name=b'Number of dimensions', validators=[django.core.validators.MinValueValidator(2), django.core.validators.MaxValueValidator(5)]),
        ),
    ]
