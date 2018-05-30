from django.core.management.base import BaseCommand, CommandError

from stats.models import Scenario
from stats.utils import run_mds


class Command(BaseCommand):
    help = 'Runs MDS for scenario'

    def add_arguments(self, parser):
        parser.add_argument('scenario', type=str)

    def handle(self, *args, **options):
        # Retrieve the Scenario from the database
        try:
            scenario = Scenario.objects.get(title=options['scenario'])
        except Scenario.DoesNotExist:
            raise CommandError('Scenario with title {} does not exist'.format(options['scenario']))

        run_mds(scenario)
