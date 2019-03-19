# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-03-19 10:10
from __future__ import unicode_literals

import annotations.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0027_auto_20181123_1228'),
    ]

    operations = [
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('xml_file', models.FileField(blank=True, upload_to=annotations.models.corpus_path)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='annotations.Document')),
                ('language', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='annotations.Language')),
            ],
        ),
    ]
