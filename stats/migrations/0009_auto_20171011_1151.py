# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0018_auto_20171010_1310'),
        ('stats', '0008_auto_20171009_1314'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='documents',
            field=models.ManyToManyField(to='annotations.Document', blank=True),
        ),
        migrations.AddField(
            model_name='scenariolanguage',
            name='other_labels',
            field=models.CharField(max_length=200, verbose_name=b'Allowed labels, comma-separated', blank=True),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='mds_dimensions',
            field=models.PositiveIntegerField(default=5, help_text=b'Number of dimensions to use in Multidimensional Scaling. Should be between 2 and 5.', verbose_name=b'Number of dimensions', validators=[django.core.validators.MinValueValidator(2), django.core.validators.MaxValueValidator(5)]),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='mds_fragments',
            field=picklefield.fields.PickledObjectField(verbose_name=b'MDS fragments', editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='mds_labels',
            field=picklefield.fields.PickledObjectField(verbose_name=b'MDS labels', editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='mds_matrix',
            field=picklefield.fields.PickledObjectField(verbose_name=b'MDS matrix', editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='mds_model',
            field=picklefield.fields.PickledObjectField(verbose_name=b'MDS model', editable=False, blank=True),
        ),
    ]
