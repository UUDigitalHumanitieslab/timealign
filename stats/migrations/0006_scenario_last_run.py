# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0005_scenariolanguage_tenses'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='last_run',
            field=models.DateTimeField(null=True),
        ),
    ]
