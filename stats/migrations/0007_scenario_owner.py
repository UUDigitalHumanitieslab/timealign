# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stats', '0006_auto_20180220_0941'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='owner',
            field=models.ForeignKey(related_name='scenarios', to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
