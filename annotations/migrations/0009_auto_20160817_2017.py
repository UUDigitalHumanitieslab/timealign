# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('annotations', '0008_auto_20160816_1843'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotation',
            name='last_modified_at',
            field=models.DateTimeField(default=datetime.datetime(2016, 8, 17, 18, 17, 53, 563000, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='annotation',
            name='last_modified_by',
            field=models.ForeignKey(related_name='last_modified_by', to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='annotation',
            name='annotated_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='annotation',
            name='annotated_by',
            field=models.ForeignKey(related_name='annotated_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='annotation',
            name='tense',
            field=models.CharField(max_length=200, verbose_name=b'Tense of translation', blank=True),
        ),
    ]
