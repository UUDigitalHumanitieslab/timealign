# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0003_auto_20170612_1329'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scenario',
            name='mds_dimensions',
            field=models.PositiveIntegerField(verbose_name=b'Number of dimensions to use in Multidimensional Scaling', validators=[django.core.validators.MinValueValidator(2), django.core.validators.MaxValueValidator(5)]),
        ),
    ]
