# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.core.management import call_command


def forwards(apps, schema_editor):
    call_command('loaddata', 'languages', app_label='annotations')

    Fragment = apps.get_model('annotations', 'Fragment')
    Language = apps.get_model('annotations', 'Language')

    for fragment in Fragment.objects.all():
        fragment.language_tmp = Language.objects.get(iso=fragment.language)
        fragment.save()


def backwards(apps, schema_editor):
    Fragment = apps.get_model('annotations', 'Fragment')

    for fragment in Fragment.objects.all():
        fragment.language = fragment.language_tmp.iso
        fragment.save()


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0013_auto_20170219_1346'),
    ]

    operations = [
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('iso', models.CharField(unique=True, max_length=2)),
                ('title', models.CharField(max_length=200)),
            ],
        ),
        migrations.AddField(
            model_name='fragment',
            name='language_tmp',
            field=models.ForeignKey(to='annotations.Language', null=True),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.RemoveField(
            model_name='fragment',
            name='speaker_language',
        ),
        migrations.RemoveField(
            model_name='fragment',
            name='language',
        ),
        migrations.RenameField(
            model_name='fragment',
            old_name='language_tmp',
            new_name='language',
        ),
        migrations.AlterField(
            model_name='fragment',
            name='language',
            field=models.ForeignKey(to='annotations.Language'),
        ),
        migrations.AddField(
            model_name='corpus',
            name='languages',
            field=models.ManyToManyField(to='annotations.Language'),
        ),
    ]
