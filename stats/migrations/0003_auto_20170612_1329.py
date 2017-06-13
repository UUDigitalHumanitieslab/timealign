# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0016_fragment_tense'),
        ('stats', '0002_scenario_dimensions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scenario',
            name='dimensions',
        ),
        migrations.AddField(
            model_name='scenario',
            name='corpus',
            field=models.ForeignKey(default=1, to='annotations.Corpus'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='scenario',
            name='mds_dimensions',
            field=models.PositiveIntegerField(default=1, verbose_name=b'Number of dimensions to use in Multidimensional Scaling', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)]),
            preserve_default=False,
        ),
    ]
