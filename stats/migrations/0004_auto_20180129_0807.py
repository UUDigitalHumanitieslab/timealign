# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0003_scenario_is_test'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='formal_structure',
            field=models.PositiveIntegerField(default=0, verbose_name=b'Formal structure', choices=[(0, b'none'), (1, b'narration'), (2, b'dialogue')]),
        ),
        migrations.AddField(
            model_name='scenario',
            name='formal_structure_strict',
            field=models.BooleanField(default=True, verbose_name=b'Require translations to be in the same formal structure'),
        ),
    ]
