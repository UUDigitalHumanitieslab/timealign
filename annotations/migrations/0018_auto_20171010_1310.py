# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0017_auto_20170617_2159'),
    ]

    operations = [
        migrations.AlterField(
            model_name='word',
            name='pos',
            field=models.CharField(max_length=50),
        ),
    ]
