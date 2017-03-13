# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0014_auto_20170227_2203'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotation',
            name='comments',
            field=models.TextField(blank=True),
        ),
    ]
