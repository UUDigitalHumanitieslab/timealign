# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0018_auto_20171010_1310'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotation',
            name='is_not_labeled_structure',
            field=models.BooleanField(default=False, verbose_name=b'The selected words in the original fragment are incorrectly marked as <em>{}</em>'),
        ),
        migrations.AddField(
            model_name='annotation',
            name='is_not_same_structure',
            field=models.BooleanField(default=False, verbose_name=b'The translated fragment is not in the same structure (dialogue/narrative) as the original fragment'),
        ),
        migrations.AddField(
            model_name='corpus',
            name='check_structure',
            field=models.BooleanField(default=False, verbose_name=b'Check for formal structure in the Annotations'),
        ),
        migrations.AddField(
            model_name='word',
            name='is_in_dialogue',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='word',
            name='is_in_dialogue_prob',
            field=models.DecimalField(default=0.0, max_digits=3, decimal_places=2),
        ),
        migrations.AlterField(
            model_name='annotation',
            name='is_no_target',
            field=models.BooleanField(default=False, verbose_name=b'The selected words in the original fragment do not form an instance of (a/an) <em>{}</em>'),
        ),
    ]
