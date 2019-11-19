# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0005_scenario_sentence_function'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scenario',
            name='sentence_function',
            field=models.PositiveIntegerField(default=0, verbose_name=b'Sentence function', choices=[(0, b'none'), (1, b'declarative'), (2, b'interrogative'), (3, b'exclamatory'), (4, b'imperative')]),
        ),
    ]
