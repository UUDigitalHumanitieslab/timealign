# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0007_auto_20160703_2056'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotation',
            name='tense',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AlterField(
            model_name='annotation',
            name='is_no_target',
            field=models.BooleanField(default=False, verbose_name=b'The selected words in the original fragment do not form a present perfect'),
        ),
    ]
