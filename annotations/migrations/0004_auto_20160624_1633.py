# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0003_auto_20160624_1618'),
    ]

    operations = [
        migrations.AlterField(
            model_name='word',
            name='lemma',
            field=models.CharField(max_length=200, blank=True),
        ),
    ]
