# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0010_auto_20161012_2212'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='corpus',
            options={'verbose_name_plural': 'Corpora'},
        ),
    ]
