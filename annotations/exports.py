from django.db.models import Count, Max

from annotations.models import Annotation, Fragment, Word
from .management.commands.utils import open_csv, open_xlsx, pad_list


def export_pos_file(filename, format_, corpus, language,
                    document=None, include_non_targets=False, add_lemmata=False):
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

        if annotations:
            header = ['id', 'tense', 'source/target', 'is correct target?', 'is correct translation?']
            header.extend(['w' + str(i + 1) for i in range(max_words)])
            header.extend(['pos' + str(i + 1) for i in range(max_words)])
            if add_lemmata:
                header.extend(['lemma' + str(i + 1) for i in range(max_words)])
            header.extend(['comments', 'full fragment', 'source words', 'source fragment'])
            writer.writerow(header, is_header=True)

            for annotation in annotations:
                words = annotation.words.all()
                w = [word.word for word in words]
                pos = [word.pos for word in words]
                lemma = [word.lemma for word in words]
                tf = annotation.alignment.translated_fragment
                of = annotation.alignment.original_fragment
                writer.writerow([annotation.pk, annotation.label(), 'target',
                                 'no' if annotation.is_no_target else 'yes',
                                 'yes' if annotation.is_translation else 'no'] +
                                pad_list(w, max_words) +
                                pad_list(pos, max_words) +
                                (pad_list(lemma, max_words) if add_lemmata else []) +
                                [annotation.comments, tf.full(), of.target_words(), of.full()])


def export_fragments_file(filename, format_, corpus, language,
                          document=None, add_lemmata=False):
    if format_ == 'xlsx':
        opener = open_xlsx
    else:
        opener = open_csv

    with opener(filename) as writer:
        fragments = Fragment.objects.filter(language__iso=language, document__corpus=corpus)

        if document is not None:
            fragments = fragments.filter(document__title=document)

        # Sort by sentence.xml_id
        fragments = sorted(fragments, key=lambda f: (map(int, f.first_sentence().xml_id[1:].split('.'))))

        if fragments:
            # TODO: see if we can do this query-based
            max_words = 0
            for fragment in fragments:
                words = Word.objects.filter(sentence__fragment=fragment, is_target=True)
                if len(words) > max_words:
                    max_words = len(words)

            header = ['id', 'label']
            header.extend(['w' + str(i + 1) for i in range(max_words)])
            header.extend(['pos' + str(i + 1) for i in range(max_words)])
            if add_lemmata:
                header.extend(['lemma' + str(i + 1) for i in range(max_words)])
            header.extend(['comments', 'full fragment'])
            writer.writerow(header, is_header=True)

            for fragment in fragments:
                words = Word.objects.filter(sentence__fragment=fragment, is_target=True)
                if words:
                    w = [word.word for word in words]
                    pos = [word.pos for word in words]
                    lemma = [word.lemma for word in words]
                    f = fragment.full()
                    writer.writerow([fragment.pk, fragment.label()] +
                                    pad_list(w, max_words) +
                                    pad_list(pos, max_words) +
                                    (pad_list(lemma, max_words) if add_lemmata else []) +
                                    ['', f])
