# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0041_alter_subsentence_xml_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='corpus',
            name='is_public',
            field=models.BooleanField(default=False, verbose_name=b'Whether this Corpus is accessible by unauthenticated users'),
        ),
    ]
