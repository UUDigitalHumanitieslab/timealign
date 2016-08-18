# -*- coding: utf-8 -*-

from __future__ import division

import pickle

from django.core.management.base import BaseCommand

from annotations.models import Annotation, Fragment


class Command(BaseCommand):
    help = 'Exports a distance matrix of all (correct) annotations'

    def handle(self, *args, **options):
        tenses = []

        for fragment in Fragment.objects.filter(language=Fragment.ENGLISH):
            annotations = Annotation.objects.filter(alignment__original_fragment=fragment, is_no_target=False)
            if annotations.count() == len(Fragment.LANGUAGES) - 1:
                tenses.append([annotation.tense for annotation in annotations])

        matrix = []
        for t1 in tenses:
            result = []
            for t2 in tenses:
                result.append(get_distance(t1, t2))
            matrix.append(result)

        pickle.dump(matrix, open('matrix.p', 'wb'))
        pickle.dump(tenses, open('tenses.p', 'wb'))


def get_distance(array1, array2):
    result = 0
    total = 0

    for i in range(len(array1)):
        if not array1[i] or not array2[i]:
            continue

        if array1[i] == array2[i]:
            result += 1

        total += 1

    return round(result / total, 2) if total > 0 else 0
