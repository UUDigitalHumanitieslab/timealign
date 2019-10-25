# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0004_auto_20180129_0807'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='sentence_function',
            field=models.PositiveIntegerField(default=0, verbose_name=b'Sentence function', choices=[(0, b'none'), (1, b'declarative'), (2, b'interrogative'), (2, b'exclamatory'), (3, b'imperative')]),
        ),
    ]
