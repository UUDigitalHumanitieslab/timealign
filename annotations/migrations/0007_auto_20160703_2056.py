# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0006_auto_20160626_1437'),
    ]

    operations = [
        migrations.AddField(
            model_name='word',
            name='is_target',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='annotation',
            name='is_no_target',
            field=models.BooleanField(default=False, verbose_name=b'There is no present perfect in the original fragment'),
        ),
        migrations.AlterField(
            model_name='annotation',
            name='words',
            field=models.ManyToManyField(to='annotations.Word', blank=True),
        ),
    ]
