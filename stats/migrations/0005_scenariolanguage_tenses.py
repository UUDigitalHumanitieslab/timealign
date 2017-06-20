# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0017_auto_20170617_2159'),
        ('stats', '0004_auto_20170617_2159'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenariolanguage',
            name='tenses',
            field=models.ManyToManyField(to='annotations.Tense'),
        ),
    ]
