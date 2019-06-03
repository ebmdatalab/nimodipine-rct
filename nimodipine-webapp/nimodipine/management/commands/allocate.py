import csv


from django.core.management.base import BaseCommand
from django.db import transaction

from nimodipine.models import Intervention


class Command(BaseCommand):
    help = '''Load interventions from practice allocations'''

    def add_arguments(self, parser):
        parser.add_argument('--allocations', required=True)

    def handle(self, *args, **options):
        methods = [x[0] for x in Intervention.METHOD_CHOICES]
        with transaction.atomic():
            with open(options['allocations'], 'r') as f:
                for a in csv.DictReader(f):
                    if a['allocation'] != 'con':  # not a control
                        for method in methods:
                            Intervention.objects.create(
                                intervention=a['group_ab'],
                                method=method,
                                practice_id=a['practice_id']
                            )
