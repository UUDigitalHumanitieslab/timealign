# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from annotations.models import Corpus, Document, Fragment, Alignment, Annotation, Label, LabelKey, Sentence, Word


def copy_fragment(fragment, source='source', target='default'):
    # Save relationships
    sentences = Sentence.objects.using(source).filter(fragment=fragment)
    labels = Label.objects.using(source).filter(fragment=fragment)
    document = fragment.document

    # Create a copy
    copy_fragment = fragment
    copy_fragment.pk = None
    copy_fragment.tense = None
    copy_fragment.save(using=target)

    # Add references
    corpus = Corpus.objects.using(target).get(title='Europarl-conditionals2')
    document, _ = Document.objects.using(target).get_or_create(corpus=corpus, title=document.title)
    copy_fragment.document = document
    copy_fragment.save(using=target)

    word_dict = dict()
    # Copy linked models
    for sentence in sentences:
        # Save relationships
        words = Word.objects.using(source).filter(sentence=sentence)

        # Create a copy
        copy_sentence = sentence
        copy_sentence.pk = None
        copy_sentence.save(using=target)

        # Add references
        copy_sentence.fragment = copy_fragment
        copy_sentence.save(using=target)

        # Copy linked models
        for word in words:
            word_pk = word.pk
            copy_word = word
            copy_word.pk = None
            copy_word.save(using=target)

            # Add references
            copy_word.sentence = copy_sentence
            copy_word.save(using=target)
            word_dict[word_pk] = copy_word.pk

    # Copy linked models
    for label in labels:
        if label.title not in ["''", 'other'] and label.key.title in ['Antecedent tense', 'Modality', 'Consequent tense']:
            new_labelkey = LabelKey.objects.using(target).get(title=label.key)
            try:
                new_label = Label.objects.using(target).get(key=new_labelkey,
                                                            language=copy_fragment.language,
                                                            title=label.title)
                copy_fragment.labels.add(new_label)
            except Label.DoesNotExist:
                print(label.key.title, label.title)

    return copy_fragment, word_dict


def copy_alignment(alignment, original_fragment, source='source', target='default'):
    # Save relationships
    annotations = Annotation.objects.using(source).filter(alignment=alignment)
    translated_fragment = alignment.translated_fragment

    # Create a copy
    copy_alignment = alignment
    copy_alignment.pk = None
    copy_alignment.save(using=target)

    # Copy linked models
    copy_translated_fragment, word_dict = copy_fragment(translated_fragment)
    copy_alignment.original_fragment = original_fragment
    copy_alignment.translated_fragment = copy_translated_fragment
    copy_alignment.save(using=target)

    for annotation in annotations:
        # Save relationships
        labels = Label.objects.using(source).filter(annotation=annotation)
        word_pks = Word.objects.using(source).filter(annotation=annotation).values_list('pk', flat=True)

        # Create a copy
        copy_annotation = annotation
        copy_annotation.pk = None
        copy_annotation.save(using=target)

        # Add references
        copy_annotation.alignment = copy_alignment
        copy_annotation.save(using=target)

        # Copy linked models
        for label in labels:
            if label.title not in ["''", 'other'] and label.key.title in ['Antecedent tense', 'Modality', 'Consequent tense']:
                new_labelkey = LabelKey.objects.using(target).get(title=label.key.title)
                try:
                    new_label = Label.objects.using(target).get(key=new_labelkey,
                                                                language=copy_translated_fragment.language,
                                                                title=label.title)
                    copy_annotation.labels.add(new_label)
                except Label.DoesNotExist:
                    print(label.key.title, label.title)

        for word_pk in word_pks:
            annotation.words.add(Word.objects.using(target).get(pk=word_dict[word_pk]))


class Command(BaseCommand):
    help = 'Copies Fragments from one database to another'
    # TODO: This is a one-off command and contains some magic strings.

    def add_arguments(self, parser):
        parser.add_argument('fragments', nargs='+', type=str)

    def handle(self, *args, **options):
        for fragment_pk in options['fragments']:
            fragment = Fragment.objects.using('source').get(pk=fragment_pk)
            alignments = Alignment.objects.using('source').filter(original_fragment=fragment,
                                                                  translated_fragment__language__iso='nl')

            copied_fragment, _ = copy_fragment(fragment)
            for alignment in alignments:
                copy_alignment(alignment, copied_fragment)

            print(fragment_pk, '=>', copied_fragment.pk)
