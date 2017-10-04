# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0006_scenario_last_run'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenariolanguage',
            name='use_other_label',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='last_run',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
