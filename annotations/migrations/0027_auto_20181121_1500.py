# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-11-21 15:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0026_auto_20181003_0851'),
    ]

    operations = [
        migrations.CreateModel(
            name='FocusSentence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('xml_id', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='FocusSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
            ],
        ),
        migrations.AddIndex(
            model_name='word',
            index=models.Index(fields=[b'xml_id'], name='annotations_xml_id_4487c7_idx'),
        ),
        migrations.AddIndex(
            model_name='sentence',
            index=models.Index(fields=[b'xml_id'], name='annotations_xml_id_9ad5bf_idx'),
        ),
        migrations.AddField(
            model_name='focusset',
            name='corpus',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='annotations.Corpus'),
        ),
        migrations.AddField(
            model_name='focusset',
            name='language',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='annotations.Language'),
        ),
        migrations.AddField(
            model_name='focussentence',
            name='document',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='annotations.Document'),
        ),
        migrations.AddField(
            model_name='focussentence',
            name='focus_set',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='annotations.FocusSet'),
        ),
        migrations.AddField(
            model_name='corpus',
            name='current_focus_set',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='current_focus_set', to='annotations.FocusSet'),
        ),
        migrations.AlterUniqueTogether(
            name='focusset',
            unique_together=set([('corpus', 'title')]),
        ),
        migrations.AlterUniqueTogether(
            name='focussentence',
            unique_together=set([('document', 'focus_set', 'xml_id')]),
        ),
    ]
