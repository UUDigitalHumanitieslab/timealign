# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0019_auto_20171129_2157'),
    ]

    operations = [
        migrations.AddField(
            model_name='fragment',
            name='formal_structure',
            field=models.PositiveIntegerField(default=0, verbose_name=b'Formal structure', choices=[(0, b'none'), (1, b'narration'), (2, b'dialogue')]),
        ),
    ]
