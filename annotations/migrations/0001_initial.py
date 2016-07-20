# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Alignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='Annotation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_translation', models.BooleanField()),
                ('annotated_at', models.DateTimeField(auto_now=True)),
                ('alignment', models.ForeignKey(to='annotations.Alignment')),
                ('annotated_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='Fragment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language', models.CharField(max_length=2, choices=[(b'de', b'German'), (b'en', b'English'), (b'es', b'Spanish'), (b'fr', b'French'), (b'nl', b'Dutch')])),
                ('speaker_language', models.CharField(max_length=2, choices=[(b'de', b'German'), (b'en', b'English'), (b'es', b'Spanish'), (b'fr', b'French'), (b'nl', b'Dutch')])),
                ('document', models.ForeignKey(to='annotations.Document')),
            ],
        ),
        migrations.CreateModel(
            name='Sentence',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('xml_id', models.CharField(max_length=20)),
                ('xml', models.TextField()),
                ('fragment', models.ForeignKey(to='annotations.Fragment')),
            ],
        ),
        migrations.CreateModel(
            name='Word',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('xml_id', models.CharField(max_length=20)),
                ('pos', models.CharField(max_length=10)),
                ('lemma', models.CharField(max_length=200)),
                ('sentence', models.ForeignKey(to='annotations.Sentence')),
            ],
        ),
        migrations.AddField(
            model_name='annotation',
            name='words',
            field=models.ManyToManyField(to='annotations.Word'),
        ),
        migrations.AddField(
            model_name='alignment',
            name='original_fragment',
            field=models.ForeignKey(related_name='original', to='annotations.Fragment', null=True),
        ),
        migrations.AddField(
            model_name='alignment',
            name='translated_fragment',
            field=models.ForeignKey(related_name='translated', to='annotations.Fragment', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='annotation',
            unique_together=set([('alignment', 'annotated_by')]),
        ),
    ]
