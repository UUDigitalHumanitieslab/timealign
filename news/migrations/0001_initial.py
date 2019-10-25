# -*- coding: utf-8 -*-


from django.db import migrations, models
import datetime
import re
import django.core.validators
import ckeditor.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(default=datetime.date.today)),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField(max_length=200, validators=[django.core.validators.RegexValidator(re.compile('^[-a-zA-Z0-9_]+\\Z'), "Enter a valid 'slug' consisting of letters, numbers, underscores or hyphens.", 'invalid')])),
                ('content', ckeditor.fields.RichTextField()),
                ('is_published', models.BooleanField(default=True, help_text=b'Untick if you want to keep this as a draft')),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
    ]
