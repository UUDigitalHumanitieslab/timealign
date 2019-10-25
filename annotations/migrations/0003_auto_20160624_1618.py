# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0002_auto_20160624_1608'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sentence',
            name='xml',
        ),
        migrations.AddField(
            model_name='word',
            name='word',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
