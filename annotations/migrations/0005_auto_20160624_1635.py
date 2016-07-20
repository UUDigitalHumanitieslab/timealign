# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0004_auto_20160624_1633'),
    ]

    operations = [
        migrations.AlterField(
            model_name='word',
            name='lemma',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
