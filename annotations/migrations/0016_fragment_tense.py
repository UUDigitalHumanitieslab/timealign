# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0015_annotation_comments'),
    ]

    operations = [
        migrations.AddField(
            model_name='fragment',
            name='tense',
            field=models.CharField(max_length=200, verbose_name=b'Tense of original', blank=True),
        ),
    ]
