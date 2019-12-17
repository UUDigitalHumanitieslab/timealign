from django.db import migrations


def migrate_labels(apps, schema_editor):
    Annotation = apps.get_model('annotations', 'Annotation')
    Fragment = apps.get_model('annotations', 'Fragment')
    Label = apps.get_model('annotations', 'Label')
    LabelCategory = apps.get_model('annotations', 'LabelCategory')

    for f in Fragment.objects.exclude(other_label=None).exclude(other_label=''):
        category, created = LabelCategory.objects.get_or_create(title='Other',
                                                                corpus=f.document.corpus)
        if created:
            category.save()

        label, created = Label.objects.get_or_create(title=f.other_label,
                                                     category=category)
        if created:
            label.save()
        f.labels.add(label)
        f.save()

    for a in Annotation.objects.exclude(other_label=None).exclude(other_label=''):
        corpus = a.alignment.original_fragment.document.corpus
        category, created = LabelCategory.objects.get_or_create(title='Other',
                                                                corpus=corpus)
        if created:
            category.save()

        label, created = Label.objects.get_or_create(title=a.other_label,
                                                     category=category)

        if created:
            label.save()
        a.labels.add(label)
        a.save()


def remove_labels(apps, schema_editor):
    Annotation = apps.get_model('annotations', 'Annotation')
    Label = apps.get_model('annotations', 'Label')
    LabelCategory = apps.get_model('annotations', 'LabelCategory')

    for a in Annotation.objects.exclude(labels=None):
        a.labels.set([])
        a.save()

    Label.objects.all().delete()
    LabelCategory.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0031_auto_20191212_1106'),
    ]

    operations = [
        migrations.RunPython(migrate_labels, remove_labels),
    ]
