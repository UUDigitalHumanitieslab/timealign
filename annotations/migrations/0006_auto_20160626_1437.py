# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0005_auto_20160624_1635'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotation',
            name='is_no_target',
            field=models.BooleanField(default=False, verbose_name=b'This is not a present perfect in the original fragment'),
        ),
        migrations.AlterField(
            model_name='annotation',
            name='is_translation',
            field=models.BooleanField(default=True, verbose_name=b'This is a correct translation of the original fragment'),
        ),
    ]
