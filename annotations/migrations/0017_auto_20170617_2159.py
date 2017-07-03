# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management import call_command
from django.db import migrations, models


class Migration(migrations.Migration):
    def load_fixtures(apps, schema_editor):
        call_command('loaddata', 'tensecategories', app_label='annotations')
        call_command('loaddata', 'tenses', app_label='annotations')

    def update_tenses(apps, schema_editor):
        Fragment = apps.get_model('annotations', 'Fragment')
        Annotation = apps.get_model('annotations', 'Annotation')
        Tense = apps.get_model('annotations', 'Tense')

        def get_alternative(language, tense):
            if language.iso == 'fr' and tense == 'futur':
                return Tense.objects.get(language=language, title='futur simple')
            if language.iso == 'fr' and tense == 'conditionnel':
                return Tense.objects.get(language=language, title='conditionnel présent')
            if language.iso == 'fr' and tense == 'RecentPast':
                return Tense.objects.get(language=language, title='passé récent')
            if language.iso == 'fr' and tense == 'Participle':
                return Tense.objects.get(language=language, title='participe présent')
            if language.iso == 'es' and tense in ['futuro', 'futuro simple']:
                return Tense.objects.get(language=language, title='futuro imperfecto')
            if language.iso == 'es' and tense == 'condicional':
                return Tense.objects.get(language=language, title='condicional simple')
            if language.iso == 'es' and tense in ['infinitivo presente', 'infinitivo simple']:
                return Tense.objects.get(language=language, title='infinitivo')
            if language.iso == 'es' and tense == 'futuro compuesto':
                return Tense.objects.get(language=language, title='futuro perfecto')
            if language.iso == 'es' and tense in ['pretérito perfecto simple', 'indefinido']:
                return Tense.objects.get(language=language, title='pretérito indefinido')
            if language.iso == 'en' and tense == 'present continous':
                return Tense.objects.get(language=language, title='present continuous')
            if tense == 'PresPerf':
                if language.iso == 'de':
                    return Tense.objects.get(language=language, title='Perfekt')
                if language.iso == 'es':
                    return Tense.objects.get(language=language, title='pretérito perfecto compuesto')
                if language.iso == 'fr':
                    return Tense.objects.get(language=language, title='passé composé')
                if language.iso == 'nl':
                    return Tense.objects.get(language=language, title='vtt')
                if language.iso == 'pt':
                    return Tense.objects.get(language=language, title='pretérito perfeito')
            if tense in ['Rep', 'Present']:
                if language.iso == 'de':
                    return Tense.objects.get(language=language, title='Präsens')
                if language.iso == 'es':
                    return Tense.objects.get(language=language, title='presente')
                if language.iso == 'fr':
                    return Tense.objects.get(language=language, title='présent')
                if language.iso == 'nl':
                    return Tense.objects.get(language=language, title='ott')
                if language.iso == 'pt':
                    return Tense.objects.get(language=language, title='pretérito')
            if tense in ['Past', 'Imperfecto']:
                if language.iso == 'de':
                    return Tense.objects.get(language=language, title='Präteritum')
                if language.iso == 'es':
                    return Tense.objects.get(language=language, title='pretérito indefinido')
                if language.iso == 'fr':
                    return Tense.objects.get(language=language, title='imparfait')
                if language.iso == 'nl':
                    return Tense.objects.get(language=language, title='ovt')
                if language.iso == 'pt':
                    return Tense.objects.get(language=language, title='pretérito imperfeito')
            if tense == 'PastPerf':
                if language.iso == 'de':
                    return Tense.objects.get(language=language, title='Plusquamperfekt')
                if language.iso == 'nl':
                    return Tense.objects.get(language=language, title='vvt')
                if language.iso == 'pt':
                    return Tense.objects.get(language=language, title='pretérito mais-que-perfeito')
            if tense in ['Gerund', 'PresGer']:
                if language.iso == 'es':
                    return Tense.objects.get(language=language, title='gerundio')
                if language.iso == 'pt':
                    return Tense.objects.get(language=language, title='gerundio')
            if tense in ['Cont', 'PresPerfGer']:
                if language.iso == 'es':
                    return Tense.objects.get(language=language, title='estar + gerundio')
                if language.iso == 'pt':
                    return Tense.objects.get(language=language, title='vir + gerundio')
            return None

        for fragment in Fragment.objects.all():
            tense = fragment.tense
            if tense:
                try:
                    language = fragment.language
                    fragment.tense_new = Tense.objects.get(language=language, title=tense)
                    fragment.save()
                except Tense.DoesNotExist:
                    t = get_alternative(language, tense)
                    if t:
                        fragment.tense_new = t
                    else:
                        fragment.tense_new = None
                    fragment.save()

        for annotation in Annotation.objects.all():
            tense = annotation.tense
            if tense:
                try:
                    language = annotation.alignment.translated_fragment.language
                    annotation.tense_new = Tense.objects.get(language=language, title=tense)
                    annotation.save()
                except Tense.DoesNotExist:
                    t = get_alternative(language, tense)
                    if t:
                        annotation.tense_new = t
                    else:
                        annotation.tense_new = None
                    annotation.save()


    dependencies = [
        ('annotations', '0016_fragment_tense'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tense',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='TenseCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=200)),
                ('color', models.CharField(max_length=10)),
            ],
            options={'verbose_name_plural': 'Tense categories'},
        ),
        migrations.AddField(
            model_name='tense',
            name='category',
            field=models.ForeignKey(to='annotations.TenseCategory'),
        ),
        migrations.AddField(
            model_name='tense',
            name='language',
            field=models.ForeignKey(to='annotations.Language'),
        ),
        migrations.AlterUniqueTogether(
            name='tense',
            unique_together=set([('language', 'title')]),
        ),

        migrations.RunPython(load_fixtures),

        migrations.AddField(
            model_name='annotation',
            name='tense_new',
            field=models.ForeignKey(to='annotations.Tense', null=True),
        ),
        migrations.AddField(
            model_name='fragment',
            name='tense_new',
            field=models.ForeignKey(to='annotations.Tense', null=True),
        ),

        migrations.RunPython(update_tenses),

        migrations.RemoveField(
            model_name='annotation',
            name='tense',
        ),
        migrations.RenameField(
            model_name='annotation',
            old_name='tense_new',
            new_name='tense',
        ),

        migrations.RemoveField(
            model_name='fragment',
            name='tense',
        ),
        migrations.RenameField(
            model_name='fragment',
            old_name='tense_new',
            new_name='tense',
        ),
    ]
