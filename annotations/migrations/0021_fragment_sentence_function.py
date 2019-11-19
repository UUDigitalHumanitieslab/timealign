# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0020_fragment_formal_structure'),
    ]

    operations = [
        migrations.AddField(
            model_name='fragment',
            name='sentence_function',
            field=models.PositiveIntegerField(default=0, verbose_name=b'Sentence function', choices=[(0, b'none'), (1, b'declarative'), (2, b'interrogative'), (2, b'exclamatory'), (3, b'imperative')]),
        ),
    ]
