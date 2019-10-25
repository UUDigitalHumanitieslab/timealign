# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0012_corpus_annotators'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='title',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterUniqueTogether(
            name='document',
            unique_together=set([('corpus', 'title')]),
        ),
    ]
