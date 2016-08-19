# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from annotations.models import Annotation, Fragment


class Command(BaseCommand):
    help = 'Automatically add tenses for existing (correct) Annotations'

    def handle(self, *args, **options):
        for annotation in Annotation.objects.filter(is_no_target=False).filter(is_translation=True):
            annotation.tense = get_tense(annotation)
            annotation.save()


def get_tense(annotation):
    language = annotation.alignment.translated_fragment.language
    words = annotation.words.all()
    pos_tags = [word.pos for word in words]

    # German POS tags do NOT discern between present and past tense :-(
    if language == Fragment.GERMAN:
        tense = get_tense_de(pos_tags)
    elif language == Fragment.ENGLISH:
        tense = get_tense_en(pos_tags)
    elif language == Fragment.SPANISH:
        tense = get_tense_es(pos_tags)
    elif language == Fragment.FRENCH:
        tense = get_tense_fr(pos_tags)
    elif language == Fragment.DUTCH:
        tense = get_tense_nl(pos_tags)

    return tense


def get_tense_de(pos_tags):
    tense = 'other'

    if len(pos_tags) == 1:
        if pos_tags[0] in ['VAFIN', 'VAINF', 'VVFIN', 'VVINF', 'VVIZU', 'VMFIN', 'VMINF']:
            tense = u'Präsens'  # Präterium?
        if pos_tags[0] in ['ADJA', 'ADJD']:
            tense = 'Adjektiv'
    elif len(pos_tags) == 2:
        # TODO: check this
        if ('VAFIN' in pos_tags or 'VAINF' in pos_tags) and (
                    'VVPP' in pos_tags or 'VVFIN' in pos_tags or 'VAPP' in pos_tags):
            tense = u'Perfect'
    elif len(pos_tags) == 3:
        if set(pos_tags) == set(['VVPP', 'VAPP', 'VAFIN']):
            tense = u'Perfect Passiv'
        elif set(pos_tags) == set(['PRF', 'VVPP', 'VAFIN']):
            tense = u'Perfect Reflexiv'

    return tense


def get_tense_en(pos_tags):
    tense = 'other'

    if len(pos_tags) == 1:
        if pos_tags[0] in ['VBZ', 'VBP', 'VDZ', 'VDP', 'VHZ', 'VHP', 'VVP', 'VVZ']:
            tense = 'simple present'
        elif pos_tags[0] in ['VBD', 'VDD', 'VHD', 'VVD']:
            tense = 'simple past'
    elif len(pos_tags) == 2:
        if pos_tags[1] in ['VBD', 'VBN', 'VDD', 'VDN', 'VHD', 'VHN', 'VVD',
                           'VVN']:  # ending in D not entirely correct, but lots of mistags here
            if pos_tags[0] in ['VH', 'VHZ', 'VHP']:
                tense = 'present perfect'
            elif pos_tags[0] == 'VHD':
                tense = 'past perfect'
            # Passive forms
            elif pos_tags[0] in ['VBZ', 'VBP']:
                tense = 'simple present'
            elif pos_tags[0] == 'VBD':
                tense = 'simple past'

        # TODO: continuous

    elif len(pos_tags) == 3:
        if pos_tags[1] == 'VBN':
            if pos_tags[2] == 'VVN':
                # Passive forms
                if pos_tags[0] in ['VHZ', 'VHP']:
                    tense = 'present perfect'
                elif pos_tags[0] == 'VHD':
                    tense = 'past perfect'
            elif pos_tags[2] == 'VVG':
                if pos_tags[0] in ['VHZ', 'VHP']:
                    tense = 'present perfect continuous'
                elif pos_tags[0] == 'VHD':
                    tense = 'past perfect continuous'

    return tense


def get_tense_es(pos_tags):
    tense = 'other'

    if len(pos_tags) == 1:
        if pos_tags[0] in ['VEfin', 'VHfin', 'VLfin', 'VMfin', 'VSfin']:
            tense = 'presente'
    if len(pos_tags) == 2:
        if pos_tags[0] == 'VHfin' and pos_tags[1] in ['VEadj', 'VHadj', 'VLadj', 'VMadj', 'VSadj']:
            tense = 'pretérito perfecto'
        elif pos_tags[0] == 'SE' and pos_tags[1] == 'VLfin':
            tense = 'presente (reflexive)'
        elif pos_tags[0] == 'VEfin' and pos_tags[1] == 'VLadj':
            tense = 'gerundio'
    if len(pos_tags) == 3:
        if pos_tags == ['SE', 'VHfin', 'VLadj']:
            tense = 'pretérito perfecto (reflexive)'
        elif pos_tags == ['VHfin', 'VSadj', 'VLadj']:
            tense = 'pretérito perfecto (processual passive)'
        elif pos_tags == ['VHfin', 'VSadj', 'VLadj']:
            tense = 'pretérito perfecto (processual passive)'
        elif pos_tags == ['VLfin', 'PREP', 'VLinf'] or pos_tags == ['VLfin', 'CSUBI', 'VLinf']:
            tense = 'simple past (acabar)'

    # if tense == 'other':
    #     print(tense, pos_tags, [word.word for word in words])

    return tense


def get_tense_fr(pos_tags):
    tense = 'other'

    if len(pos_tags) == 1:
        if pos_tags[0] in ['VER:pres', 'VER:subp']:
            tense = u'présent'
        elif pos_tags[0] in ['VER:impf', 'VER:subi']:  # does this happen?
            tense = u'imparfait'
        elif pos_tags[0] == 'VER:simp':
            tense = u'passé simple'
        elif pos_tags[0] == 'VER:futu':
            tense = u'futur'
        elif pos_tags[0] == 'VER:cond':
            tense = u'conditionnel'
    elif len(pos_tags) == 2:
        if pos_tags[1] == 'VER:pper':
            if pos_tags[0] in ['VER:pres', 'VER:subp']:
                tense = u'passé composé'
            elif pos_tags[0] == 'VER:impf':
                tense = u'plus-que-parfait'
            elif pos_tags[0] == 'VER:simp':
                tense = u'passé antérieur'
            elif pos_tags[0] == 'VER:futu':
                tense = u'futur antérieur'
            elif pos_tags[0] == 'VER:cond':
                tense = u'conditionnel passé'
    elif len(pos_tags) == 3:
        # Passive forms
        if pos_tags == ['VER:pres', 'VER:pper', 'VER:pper']:
            tense = u'passé composé'
        if pos_tags == ['VER:subp', 'VER:pper', 'VER:pper']:
            tense = u'passé composé'
        if pos_tags == ['VER:impf', 'VER:pper', 'VER:pper']:
            tense = u'plus-que-parfait'
        # Reflexives
        if pos_tags == ['PRO:PER', 'VER:pres', 'VER:pper']:
            tense = u'passé composé'
        if pos_tags == ['PRO:PER', 'VER:subp', 'VER:pper']:
            tense = u'passé composé'
        # Example: Je viens de chanter
        if pos_tags == ['VER:pres', 'PRP', 'VER:infi']:
            tense = u'passé récent'

    return tense


def get_tense_nl(pos_tags):
    tense = 'other'

    # Check passives?!

    if 'verbpressg' in pos_tags or 'verbprespl' in pos_tags or 'verbinf' in pos_tags:
        tense = 'vtt' if 'verbpapa' in pos_tags else 'ott'
    elif 'verbpastsg' in pos_tags or 'verbpastpl' in pos_tags:
        tense = 'vvt' if 'verbpapa' in pos_tags else 'ovt'

    return tense
