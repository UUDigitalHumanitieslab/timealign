# -*- coding: utf-8 -*-

import codecs

from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand

from core.utils import unicode_csv_reader


class Command(BaseCommand):
    help = 'Imports Users from a .csv-file'

    def add_arguments(self, parser):
        parser.add_argument('filenames', nargs='+', type=str)
        parser.add_argument('--group', dest='group', help='Group')

    def handle(self, *args, **options):
        for filename in options['filenames']:
            with codecs.open(filename, 'r', 'utf-8') as csvfile:
                csv_reader = unicode_csv_reader(csvfile, delimiter=';')
                next(csv_reader)  # skip header

                for row in csv_reader:
                    if row:
                        # username, email, password, first_name, last_name
                        user = User.objects.create_user(row[0], row[1], row[2])
                        user.first_name = row[3]
                        user.last_name = row[4]
                        user.save()

                        if options['group']:
                            group, _ = Group.objects.get_or_create(name=options['group'])
                            group.user_set.add(user)
                            group.save()
