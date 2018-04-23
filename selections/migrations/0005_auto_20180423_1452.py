# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('selections', '0004_auto_20180129_0807'),
    ]

    operations = [
        migrations.AlterField(
            model_name='selection',
            name='is_no_target',
            field=models.BooleanField(default=False, verbose_name=b'This fragment does not contain a target'),
        ),
    ]
