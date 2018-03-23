from django.db.models import Count, Max
import numbers

from annotations.models import Annotation, Fragment, Word
from .management.commands.utils import open_csv, open_xlsx, pad_list


def export_pos_file(filename, format_, corpus, language, document=None, add_sources=False, include_non_targets=False):
    if format_ == 'xlsx':
        opener = open_xlsx
    else:
        opener = open_csv

    with opener(filename) as writer:
        annotations = Annotation.objects. \
            filter(alignment__translated_fragment__language__iso=language,
                   alignment__translated_fragment__document__corpus=corpus)

        if not include_non_targets:
            annotations = annotations.filter(is_no_target=False, is_translation=True)

        if document is not None:
            annotations = annotations.filter(alignment__translated_fragment__document__title=document)

        annotations = annotations.select_related().annotate(selected_words=Count('words'))
        max_words = annotations.aggregate(Max('selected_words'))['selected_words__max']

        header = ['id', 'tense', 'source/target', 'is correct target?', 'is correct translation?']
        header.extend(['w' + str(i + 1) for i in range(max_words)])
        header.extend(['pos' + str(i + 1) for i in range(max_words)])
        header.extend(['comments', 'full fragment', 'source words', 'source fragment'])
        writer.writerow(header, is_header=True)

        for annotation in annotations:
            words = annotation.words.all()
            w = [word.word for word in words]
            pos = [word.pos for word in words]
            tf = annotation.alignment.translated_fragment
            of = annotation.alignment.original_fragment
            writer.writerow([annotation.pk, annotation.label(), 'target',
                             'no' if annotation.is_no_target else 'yes',
                             'yes' if annotation.is_translation else 'no'] +
                            pad_list(w, max_words) +
                            pad_list(pos, max_words) +
                            [annotation.comments, tf.full(), of.target_words(), of.full()])

        if add_sources:
            fragments = Fragment.objects.filter(language__iso=language, document__corpus=corpus)
            for fragment in fragments:
                words = Word.objects.filter(sentence__fragment=fragment, is_target=True)
                if words:
                    w = [word.word for word in words]
                    pos = [word.pos for word in words]
                    f = fragment.full()
                    writer.writerow([fragment.pk, fragment.tense.title, 'source', '', ''] +
                                    pad_list(w, 8) +
                                    pad_list(pos, 8) +
                                    ['', f, '', ''])
