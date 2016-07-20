# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='date',
        ),
        migrations.AlterField(
            model_name='document',
            name='title',
            field=models.CharField(unique=True, max_length=200),
        ),
    ]
