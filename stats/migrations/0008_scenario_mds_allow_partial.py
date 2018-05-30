# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0007_scenario_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='mds_allow_partial',
            field=models.BooleanField(default=False, help_text=b'When enabled, the model will include tuples where one or more of the target languages have no Annotation', verbose_name=b'Allow partial tuples in model'),
        ),
    ]
