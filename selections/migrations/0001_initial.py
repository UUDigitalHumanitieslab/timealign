# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('annotations', '0014_auto_20170227_2203'),
    ]

    operations = [
        migrations.CreateModel(
            name='PreProcessFragment',
            fields=[
                ('fragment_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='annotations.Fragment')),
            ],
            bases=('annotations.fragment',),
        ),
        migrations.CreateModel(
            name='Selection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_no_target', models.BooleanField(default=False, verbose_name=b'This fragment does not contain a verb phrase')),
                ('selected_at', models.DateTimeField(auto_now_add=True)),
                ('last_modified_at', models.DateTimeField(auto_now=True)),
                ('fragment', models.ForeignKey(to='selections.PreProcessFragment')),
                ('last_modified_by', models.ForeignKey(related_name='selection_last_modified_by', to=settings.AUTH_USER_MODEL, null=True)),
                ('selected_by', models.ForeignKey(related_name='selected_by', to=settings.AUTH_USER_MODEL)),
                ('words', models.ManyToManyField(to='annotations.Word', blank=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='selection',
            unique_together=set([('fragment', 'selected_by')]),
        ),
    ]
