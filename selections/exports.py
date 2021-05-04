from django.db.models import Count, Max

from annotations.exports import labels_fixed
from annotations.management.commands.utils import open_csv, open_xlsx, pad_list
from core.utils import CSV, XLSX

from .models import Selection


def export_selections(filename, format_, corpus, language,
                      document=None, add_lemmata=False):
    if format_ == XLSX:
        opener = open_xlsx
    else:
        opener = open_csv

    with opener(filename) as writer:
        # Retrieve selections
        selections = Selection.objects. \
            filter(fragment__language__iso=language,
                   fragment__document__corpus=corpus)

        if document is not None:
            selections = selections.filter(fragment__document=document)

        selections = selections \
            .select_related('fragment__document', 'tense') \
            .prefetch_related('fragment__sentence_set__word_set', 'words') \
            .annotate(annotated_words=Count('words'))
        max_words = selections.aggregate(Max('annotated_words'))['annotated_words__max']

        # Sort by sentence.xml_id and order
        selections = sorted(selections, key=lambda s: (s.fragment.document.title, s.fragment.sort_key(), s.order))

        label_keys = corpus.label_keys.values_list('id', flat=True)
        label_keys_titles = list(corpus.label_keys.values_list('title', flat=True))
        # Output to csv/xlsx
        if selections:
            header = get_header(max_words, add_lemmata, label_keys_titles)
            writer.writerow(header, is_header=True) if format_ == XLSX else writer.writerow(header)

            for selection in selections:
                writer.writerow(get_row(selection, add_lemmata, max_words, label_keys))


def get_header(max_words, add_lemmata, label_keys_titles):
    header = ['id', 'tense']
    header.extend(label_keys_titles)
    header.extend(['has target?'])
    header.extend(['w' + str(i + 1) for i in range(max_words)])
    header.extend(['pos' + str(i + 1) for i in range(max_words)])
    if add_lemmata:
        header.extend(['lemma' + str(i + 1) for i in range(max_words)])

    header.extend(['comments', 'document', 'sentence id', 'order', 'sentence full'])

    return header


def get_row(selection, add_lemmata, max_words, label_keys):
    s_details = [selection.pk, selection.tense.title if selection.tense else '']
    s_details.extend(labels_fixed(selection, label_keys))
    s_details.append('no' if selection.is_no_target else 'yes')

    words = selection.words.all()
    w = [word.word for word in words]
    pos = [word.pos for word in words]
    lemma = [word.lemma for word in words]
    w_details = pad_list(w, max_words) + pad_list(pos, max_words) + (pad_list(lemma, max_words) if add_lemmata else [])

    fragment = selection.fragment
    f_details = [selection.comments, fragment.document.title, fragment.first_sentence().xml_id,
                 selection.order, fragment.full(CSV, selection)]

    return s_details + w_details + f_details
