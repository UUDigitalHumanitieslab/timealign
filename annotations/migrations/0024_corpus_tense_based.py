# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0023_auto_20180314_1340'),
    ]

    operations = [
        migrations.AddField(
            model_name='corpus',
            name='tense_based',
            field=models.BooleanField(default=True, verbose_name=b'Whether this Corpus is annotated for tense/aspect, or something else'),
        ),
    ]
