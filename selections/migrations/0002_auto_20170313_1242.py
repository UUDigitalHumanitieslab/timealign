# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('selections', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='selection',
            options={'get_latest_by': 'order'},
        ),
    ]
