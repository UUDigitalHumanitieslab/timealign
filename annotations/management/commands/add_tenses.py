# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from annotations.models import Annotation, Fragment


class Command(BaseCommand):
    help = 'Automatically add tenses for existing (correct) Annotations'

    def handle(self, *args, **options):
        for annotation in Annotation.objects.filter(is_no_target=False).filter(is_translation=True):
            annotation.tense = self.get_tense(annotation)
            # annotation.save()

    @staticmethod
    def get_tense(annotation):
        language = annotation.alignment.translated_fragment.language
        words = annotation.words.all()
        pos_tags = [word.pos for word in words]

        tense = 'other'
        if language == Fragment.FRENCH:
            if len(pos_tags) == 1:
                if pos_tags[0] == 'VER:pres':
                    tense = u'présent'
            elif pos_tags[0] == 'VER:pres' and pos_tags[1] == 'VER:pper' in pos_tags:
                tense = u'passé composé'

        if language == Fragment.GERMAN:
            if len(pos_tags) == 1:
                if pos_tags[0] in ['VAFIN', 'VVFIN']:
                    tense = u'Präsens'
            elif len(pos_tags) == 2 and 'VAFIN' in pos_tags and 'VVPP' in pos_tags:
                tense = u'Perfect'

        if language == Fragment.ENGLISH:
            if len(pos_tags) == 1:
                if pos_tags[0] == 'VVZ':
                    tense = 'simple present'
                elif pos_tags[0] == 'VVD':
                    tense = 'simple past'

            if tense == 'other':
                print tense, pos_tags, [word.word for word in words]

        elif language == Fragment.DUTCH:
            if 'verbpressg' in pos_tags or 'verbprespl' in pos_tags:
                tense = 'vtt' if 'verbpapa' in pos_tags else 'ott'
            elif 'verbpastsg' in pos_tags or 'verbpastpl' in pos_tags:
                tense = 'vvt' if 'verbpapa' in pos_tags else 'ovt'
            # else:
            # print tense, pos_tags, [word.word for word in words]


        return tense
