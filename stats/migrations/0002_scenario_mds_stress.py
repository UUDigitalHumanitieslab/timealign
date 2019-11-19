# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='mds_stress',
            field=models.FloatField(null=True, verbose_name=b'MDS stress'),
        ),
    ]
