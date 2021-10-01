# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0021_set_normalized_stress'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='is_public',
            field=models.BooleanField(default=False, verbose_name=b'Whether this Scenario is accessible by unauthenticated users'),
        ),
    ]
