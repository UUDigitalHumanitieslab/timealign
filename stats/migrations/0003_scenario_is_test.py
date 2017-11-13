# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0002_scenario_mds_stress'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='is_test',
            field=models.BooleanField(default=False, help_text=b'Checking this box signals that the scenario should not be displayed in the standard overview.', verbose_name=b'Test scenario'),
        ),
    ]
