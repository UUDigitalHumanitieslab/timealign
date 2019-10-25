# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('selections', '0002_auto_20170313_1242'),
    ]

    operations = [
        migrations.AddField(
            model_name='selection',
            name='comments',
            field=models.TextField(blank=True),
        ),
    ]
