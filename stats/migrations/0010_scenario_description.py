# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0009_auto_20171011_1151'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='description',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
