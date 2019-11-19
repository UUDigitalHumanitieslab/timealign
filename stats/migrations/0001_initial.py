# -*- coding: utf-8 -*-


from django.db import migrations, models
import django.core.validators
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0018_auto_20171010_1310'),
    ]

    operations = [
        migrations.CreateModel(
            name='Scenario',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('mds_dimensions', models.PositiveIntegerField(default=5, help_text=b'Number of dimensions to use in Multidimensional Scaling. Should be between 2 and 5.', verbose_name=b'Number of dimensions', validators=[django.core.validators.MinValueValidator(2), django.core.validators.MaxValueValidator(5)])),
                ('mds_model', picklefield.fields.PickledObjectField(verbose_name=b'MDS model', editable=False, blank=True)),
                ('mds_matrix', picklefield.fields.PickledObjectField(verbose_name=b'MDS matrix', editable=False, blank=True)),
                ('mds_fragments', picklefield.fields.PickledObjectField(verbose_name=b'MDS fragments', editable=False, blank=True)),
                ('mds_labels', picklefield.fields.PickledObjectField(verbose_name=b'MDS labels', editable=False, blank=True)),
                ('last_run', models.DateTimeField(null=True, blank=True)),
                ('corpus', models.ForeignKey(to='annotations.Corpus', on_delete=models.CASCADE)),
                ('documents', models.ManyToManyField(to='annotations.Document', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ScenarioLanguage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('as_from', models.BooleanField()),
                ('as_to', models.BooleanField()),
                ('use_other_label', models.BooleanField(default=False)),
                ('other_labels', models.CharField(max_length=200, verbose_name=b'Allowed labels, comma-separated', blank=True)),
                ('language', models.ForeignKey(to='annotations.Language', on_delete=models.CASCADE)),
                ('scenario', models.ForeignKey(to='stats.Scenario', on_delete=models.CASCADE)),
                ('tenses', models.ManyToManyField(to='annotations.Tense', blank=True)),
            ],
        ),
    ]
