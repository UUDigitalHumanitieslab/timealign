from django.db.models import Count, Max

from selections.models import Selection
from annotations.management.commands.utils import open_csv, open_xlsx, pad_list


def export_selections(filename, format_, corpus, language,
                      document=None, add_lemmata=False):
    if format_ == 'xlsx':
        opener = open_xlsx
    else:
        opener = open_csv

    with opener(filename) as writer:
        # Retrieve selections
        selections = Selection.objects. \
            filter(fragment__language__iso=language,
                   fragment__document__corpus=corpus)

        if document is not None:
            selections = selections.filter(fragment__document__title=document)

        selections = selections.select_related().annotate(annotated_words=Count('words'))
        max_words = selections.aggregate(Max('annotated_words'))['annotated_words__max']

        # Sort by sentence.xml_id and order
        selections = sorted(selections, key=lambda s: (map(int, s.fragment.first_sentence().xml_id[1:].split('.')),
                                                       s.order))

        # Output to csv/xlsx
        if selections:
            writer.writerow(get_header(max_words, add_lemmata), is_header=True)

            for selection in selections:
                writer.writerow(get_row(selection, add_lemmata, max_words))


def get_header(max_words, add_lemmata):
    header = ['id', 'label', 'has target?']

    header.extend(['w' + str(i + 1) for i in range(max_words)])
    header.extend(['pos' + str(i + 1) for i in range(max_words)])
    if add_lemmata:
        header.extend(['lemma' + str(i + 1) for i in range(max_words)])

    header.extend(['comments', 'order', 'sentence id', 'sentence full'])

    return header


def get_row(selection, add_lemmata, max_words):
    s_details = [selection.pk, selection.tense, 'no' if selection.is_no_target else 'yes']

    words = selection.words.all()
    w = [word.word for word in words]
    pos = [word.pos for word in words]
    lemma = [word.lemma for word in words]
    w_details = pad_list(w, max_words) + pad_list(pos, max_words) + (pad_list(lemma, max_words) if add_lemmata else [])

    fragment = selection.fragment
    f_details = [selection.comments, selection.order, fragment.first_sentence().xml_id, fragment.full()]

    return s_details + w_details + f_details
