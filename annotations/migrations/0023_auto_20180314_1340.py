# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0022_auto_20180220_0941'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='corpus',
            field=models.ForeignKey(related_name='documents', to='annotations.Corpus'),
        ),
    ]
