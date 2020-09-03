from django.db.models import Count, Max

from annotations.models import Annotation, Fragment, Word
from core.utils import XLSX

from .management.commands.utils import open_csv, open_xlsx, pad_list


def labels_fixed(annotation, label_keys):
    """
    Always returns as many labels as configured in the corpus.
    If the annotation is missing any of the required labels it will is replaced
    with an empty string.
    """
    labels = dict(annotation.labels.order_by('key').values_list('key', 'title'))
    return [labels.get(key, '') for key in label_keys]


def export_pos_file(filename, format_, corpus, language, subcorpus=None,
                    document=None, include_non_targets=False, add_lemmata=False, add_indices=False, formal_structure=None):
    if format_ == XLSX:
        opener = open_xlsx
    else:
        opener = open_csv

    with opener(filename) as writer:
        annotations = Annotation.objects. \
            filter(alignment__translated_fragment__language__iso=language,
                   alignment__translated_fragment__document__corpus=corpus)

        if not include_non_targets:
            annotations = annotations.filter(is_no_target=False, is_translation=True)

        if subcorpus:
            annotations = annotations.filter(alignment__original_fragment__in=subcorpus.get_fragments())

        if document:
            annotations = annotations.filter(alignment__translated_fragment__document=document)

        if formal_structure:
            if formal_structure == 'narration':
                annotations = annotations.filter(alignment__original_fragment__formal_structure=Fragment.FS_NARRATION)
            if formal_structure == 'dialogue':
                annotations = annotations.filter(alignment__original_fragment__formal_structure=Fragment.FS_DIALOGUE)

        max_words = annotations.annotate(selected_words=Count('words')).aggregate(Max('selected_words'))['selected_words__max']
        label_keys = corpus.label_keys.values_list('id', flat=True)
        label_keys_titles = list(corpus.label_keys.values_list('title', flat=True))

        annotations = annotations. \
            select_related('alignment__original_fragment',
                           'alignment__original_fragment__document',
                           'alignment__original_fragment__tense',
                           'alignment__translated_fragment',
                           'tense'). \
            prefetch_related('words',
                             'alignment__original_fragment__sentence_set__word_set',
                             'alignment__translated_fragment__sentence_set__word_set')

        # Sort by document and sentence.xml_id
        # TODO: This is potentially slowing down the export
        annotations = sorted(annotations, key=lambda a: (a.alignment.original_fragment.document.title,
                                                         a.alignment.original_fragment.sort_key()))

        if annotations:
            header = ['id', 'tense']
            header.extend(label_keys_titles)
            header.extend(['is correct target?', 'is correct translation?'])
            header.extend(['w' + str(i + 1) for i in range(max_words)])
            header.extend(['pos' + str(i + 1) for i in range(max_words)])
            if add_lemmata:
                header.extend(['lemma' + str(i + 1) for i in range(max_words)])
            if add_indices:
                header.extend(['index' + str(i + 1) for i in range(max_words)])
            header.extend(['comments', 'full fragment'])
            header.extend(list(['source ' + x for x in ['id', 'document', 'sentences', 'words', 'tense'] + label_keys_titles + ['fragment']]))
            writer.writerow(header, is_header=True) if format_ == XLSX else writer.writerow(header)

            # TODO: all Fragment.full() calls below are potentially slowing down the export
            for annotation in annotations:
                words = annotation.words.all()
                w = [word.word for word in words]
                pos = [word.pos for word in words]
                tf = annotation.alignment.translated_fragment
                of = annotation.alignment.original_fragment
                of_details = [of.pk, of.document.title, of.xml_ids(), of.target_words(),
                              of.tense.title if of.tense else ''] + labels_fixed(of, label_keys) + [of.full(format_)]
                writer.writerow([annotation.pk,
                                 annotation.tense.title if annotation.tense else ''] +
                                labels_fixed(annotation, label_keys) +
                                ['no' if annotation.is_no_target else 'yes',
                                 'yes' if annotation.is_translation else 'no'] +
                                pad_list(w, max_words) +
                                pad_list(pos, max_words) +
                                (pad_list([word.lemma for word in words], max_words) if add_lemmata else []) +
                                (pad_list([word.index() for word in words], max_words) if add_indices else []) +
                                [annotation.comments, tf.full(format_, annotation)] +
                                of_details)


def export_fragments_file(filename, format_, corpus, language,
                          document=None, add_lemmata=False, add_indices=False, formal_structure=None):
    if format_ == XLSX:
        opener = open_xlsx
    else:
        opener = open_csv

    with opener(filename) as writer:
        fragments = Fragment.objects.filter(language__iso=language, document__corpus=corpus)

        if document is not None:
            fragments = fragments.filter(document__title=document)

        if formal_structure:
            if formal_structure == 'narration':
                fragments = fragments.filter(formal_structure=Fragment.FS_NARRATION)
            if formal_structure == 'dialogue':
                fragments = fragments.filter(formal_structure=Fragment.FS_DIALOGUE)

        # Sort by document and sentence.xml_id
        fragments = sorted(fragments, key=lambda f: (f.document.title, f.sort_key()))

        if fragments:
            # TODO: see if we can do this query-based
            max_words = 0
            for fragment in fragments:
                words = Word.objects.filter(sentence__fragment=fragment, is_target=True)
                if len(words) > max_words:
                    max_words = len(words)

            header = ['id', 'tense', 'other label']
            header.extend(['w' + str(i + 1) for i in range(max_words)])
            header.extend(['pos' + str(i + 1) for i in range(max_words)])
            if add_lemmata:
                header.extend(['lemma' + str(i + 1) for i in range(max_words)])
            if add_indices:
                header.extend(['index' + str(i + 1) for i in range(max_words)])
            header.extend(['document', 'sentence id', 'target ids', 'full fragment'])
            writer.writerow(header, is_header=True) if format_ == XLSX else writer.writerow(header)

            for fragment in fragments:
                words = Word.objects.filter(sentence__fragment=fragment, is_target=True)
                if words:
                    w = [word.word for word in words]
                    pos = [word.pos for word in words]
                    f = fragment.full(format_)
                    writer.writerow([fragment.pk,
                                     fragment.tense.title if fragment.tense else '',
                                     fragment.other_label] +
                                    pad_list(w, max_words) +
                                    pad_list(pos, max_words) +
                                    (pad_list([word.lemma for word in words], max_words) if add_lemmata else []) +
                                    (pad_list([word.index() for word in words], max_words) if add_indices else []) +
                                    [fragment.document.title, fragment.first_sentence().xml_id, fragment.target_words(), f])
