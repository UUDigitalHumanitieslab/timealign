# -*- coding: utf-8 -*-


from django.core.management import call_command
from django.db import migrations, models


class Migration(migrations.Migration):
    def load_fixtures(apps, schema_editor):
        call_command('loaddata', 'tensecategories', app_label='annotations')
        call_command('loaddata', 'tenses', app_label='annotations')

    def update_tenses(apps, schema_editor):
        Fragment = apps.get_model('annotations', 'Fragment')
        Alignment = apps.get_model('annotations', 'Alignment')
        Annotation = apps.get_model('annotations', 'Annotation')
        Tense = apps.get_model('annotations', 'Tense')

        def get_alignments(fragment, as_original=False, as_translation=False):
            alignments = Alignment.objects.none()
            if as_original:
                alignments |= Alignment.objects.filter(original_fragment=fragment)
            if as_translation:
                alignments |= Alignment.objects.filter(translated_fragment=fragment)
            return alignments

        def get_default_tense(corpus, language):
            result = None
            if corpus == 'EuroParl-ppc':
                result = 'present perfect continuous'
            else:
                if language == 'de':
                    result = 'Perfekt'
                elif language == 'es':
                    result = 'pretérito perfecto compuesto'
                elif language == 'en':
                    result = 'present perfect'
                elif language == 'fr':
                    result = 'passé composé'
                elif language == 'nl':
                    result = 'vtt'
            return result

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
            if not fragment.tense and get_alignments(fragment, as_original=True).count() > 0:
                if get_alignments(fragment, as_translation=True).count() == 0:
                    fragment.tense = get_default_tense(fragment.document.corpus.title, fragment.language.iso)
                    fragment.save()

            tense = fragment.tense
            if tense:
                try:
                    language = fragment.language
                    fragment.tense_new = Tense.objects.get(language=language, title=tense).pk
                    fragment.save()
                except Tense.DoesNotExist:
                    t = get_alternative(language, tense)
                    if t:
                        fragment.tense_new = t.pk
                    else:
                        fragment.tense_new = None
                        fragment.other_label = tense
                    fragment.save()

        for annotation in Annotation.objects.all():
            tense = annotation.tense
            if tense:
                try:
                    language = annotation.alignment.translated_fragment.language
                    annotation.tense_new = Tense.objects.get(language=language, title=tense).pk
                    annotation.save()
                except Tense.DoesNotExist:
                    t = get_alternative(language, tense)
                    if t:
                        annotation.tense_new = t.pk
                    else:
                        annotation.tense_new = None
                        annotation.other_label = tense
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
            field=models.ForeignKey(to='annotations.TenseCategory', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='tense',
            name='language',
            field=models.ForeignKey(to='annotations.Language', on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='tense',
            unique_together=set([('language', 'title')]),
        ),

        migrations.RunPython(load_fixtures),

        migrations.AddField(
            model_name='annotation',
            name='other_label',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='annotation',
            name='tense_new',
            field=models.IntegerField(db_column='tense_new', null=True),
        ),
        migrations.AddField(
            model_name='fragment',
            name='other_label',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='fragment',
            name='tense_new',
            field=models.IntegerField(db_column='tense_new', null=True),
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
        migrations.AlterField(
            model_name='annotation',
            name='tense',
            field=models.ForeignKey(to='annotations.Tense', null=True, on_delete=models.CASCADE),
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
        migrations.AlterField(
            model_name='fragment',
            name='tense',
            field=models.ForeignKey(to='annotations.Tense', null=True, on_delete=models.CASCADE),
        ),
    ]
