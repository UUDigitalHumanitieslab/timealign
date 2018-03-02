from annotations.models import Annotation, Fragment, Word

from .management.commands.utils import open_csv, open_xlsx, pad_list


def export_pos_file(filename, format_, corpus, language, document=None, add_sources=False):
    if format_ == 'xlsx':
        opener = open_xlsx
    else:
        opener = open_csv

    with opener(filename) as writer:
        header = ['id', 'tense', 'source/target',
                  'w1', 'w2', 'w3', 'w4', 'w5', 'w6', 'w7', 'w8',
                  'pos1', 'pos2', 'pos3', 'pos4', 'pos5', 'pos6', 'pos7', 'pos8', 'comments',
                  'full fragment', 'source words', 'source fragment']
        writer.writerow(header)

        annotations = Annotation.objects. \
            filter(is_no_target=False, is_translation=True,
                   alignment__translated_fragment__language__iso=language,
                   alignment__translated_fragment__document__corpus=corpus)

        if document is not None:
            annotations = annotations.filter(alignment__translated_fragment__document__title=document)

        for annotation in annotations:
            words = annotation.words.all()
            w = [word.word for word in words]
            pos = [word.pos for word in words]
            tf = annotation.alignment.translated_fragment
            of = annotation.alignment.original_fragment
            writer.writerow([str(annotation.pk), annotation.label(), 'target'] +
                            pad_list(w, 8) +
                            pad_list(pos, 8) +
                            [annotation.comments, tf.full(), of.target_words(), of.full()])

        if add_sources:
            fragments = Fragment.objects.filter(language__iso=language, document__corpus=corpus)
            for fragment in fragments:
                words = Word.objects.filter(sentence__fragment=fragment, is_target=True)
                if words:
                    w = [word.word for word in words]
                    pos = [word.pos for word in words]
                    f = fragment.full()
                    writer.writerow([str(fragment.pk), fragment.tense.title, 'source'] +
                                    pad_list(w, 8) +
                                    pad_list(pos, 8) +
                                    ['', f, '', ''])
