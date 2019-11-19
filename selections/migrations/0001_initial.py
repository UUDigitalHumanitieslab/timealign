# -*- coding: utf-8 -*-


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
                ('fragment_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='annotations.Fragment', on_delete=models.CASCADE)),
            ],
            bases=('annotations.fragment',),
        ),
        migrations.CreateModel(
            name='Selection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_no_target', models.BooleanField(default=False, verbose_name=b'This fragment does not contain a verb phrase')),
                ('order', models.PositiveIntegerField(default=1)),
                ('is_final', models.BooleanField(default=True)),
                ('selected_at', models.DateTimeField(auto_now_add=True)),
                ('last_modified_at', models.DateTimeField(auto_now=True)),
                ('tense', models.CharField(max_length=200, verbose_name=b'Tense', blank=True)),
                ('fragment', models.ForeignKey(to='selections.PreProcessFragment', on_delete=models.CASCADE)),
                ('last_modified_by', models.ForeignKey(related_name='selection_last_modified_by', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('selected_by', models.ForeignKey(related_name='selected_by', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('words', models.ManyToManyField(to='annotations.Word', blank=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='selection',
            unique_together=set([('fragment', 'selected_by', 'order')]),
        ),
    ]
