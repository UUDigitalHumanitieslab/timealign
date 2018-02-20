# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0021_fragment_sentence_function'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fragment',
            name='sentence_function',
            field=models.PositiveIntegerField(default=0, verbose_name=b'Sentence function', choices=[(0, b'none'), (1, b'declarative'), (2, b'interrogative'), (3, b'exclamatory'), (4, b'imperative')]),
        ),
    ]
