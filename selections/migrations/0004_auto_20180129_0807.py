# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('selections', '0003_selection_comments'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='selection',
            options={'ordering': ('-selected_at',), 'get_latest_by': 'order'},
        ),
    ]
