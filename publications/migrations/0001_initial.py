# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-08-21 09:36
from __future__ import unicode_literals

import datetime
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Programme',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Thesis',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=datetime.date.today)),
                ('title', models.CharField(max_length=200)),
                ('authors_alt', models.CharField(blank=True, help_text='If the author is not a registered User, please supply an author name here', max_length=200, verbose_name='Author(s) display name')),
                ('description', models.CharField(help_text='Short description, e.g. "investigated the semantics and pragmatics of the Greek perfect"', max_length=200)),
                ('level', models.CharField(choices=[('BA', 'Bachelor'), ('MA', 'Master'), ('IN', 'Internship report')], default='BA', max_length=2)),
                ('url', models.URLField(blank=True, verbose_name='Link to thesis in thesis archive')),
                ('document', models.FileField(blank=True, help_text='Use this only if there is no archived version available', upload_to=b'', validators=[django.core.validators.FileExtensionValidator(['pdf'])])),
                ('appendix', models.FileField(blank=True, help_text='Use this only if there is no archived version available', upload_to=b'', validators=[django.core.validators.FileExtensionValidator(['pdf'])])),
                ('authors', models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL)),
                ('programme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='publications.Programme')),
            ],
            options={
                'ordering': ['-date'],
                'abstract': False,
                'verbose_name_plural': 'Theses',
            },
        ),
    ]
