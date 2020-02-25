from django.db import migrations


def migrate_labels(apps, schema_editor):
    Annotation = apps.get_model('annotations', 'Annotation')
    Fragment = apps.get_model('annotations', 'Fragment')
    Label = apps.get_model('annotations', 'Label')
    LabelKey = apps.get_model('annotations', 'LabelKey')

    for f in Fragment.objects.exclude(other_label=None).exclude(other_label=''):
        corpus = f.document.corpus
        key, created = LabelKey.objects.get_or_create(title='Other ({})'.format(corpus.title))
        key.corpora.add(corpus)
        if created:
            key.save()

        label, created = Label.objects.get_or_create(title=f.other_label,
                                                     key=key)
        if created:
            label.save()
        f.labels.add(label)
        f.save()

    for a in Annotation.objects.exclude(other_label=None).exclude(other_label=''):
        corpus = a.alignment.original_fragment.document.corpus
        key, created = LabelKey.objects.get_or_create(title='Other ({})'.format(corpus.title))
        key.corpora.add(corpus)
        if created:
            key.save()

        label, created = Label.objects.get_or_create(title=a.other_label,
                                                     key=key)

        if created:
            label.save()
        a.labels.add(label)
        a.save()


def remove_labels(apps, schema_editor):
    Annotation = apps.get_model('annotations', 'Annotation')
    Label = apps.get_model('annotations', 'Label')
    LabelKey = apps.get_model('annotations', 'LabelKey')

    for a in Annotation.objects.exclude(labels=None):
        a.labels.set([])
        a.save()

    Label.objects.all().delete()
    LabelKey.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0031_auto_20200107_2217'),
    ]

    operations = [
        migrations.RunPython(migrate_labels, remove_labels),
    ]
