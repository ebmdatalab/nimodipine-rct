import csv


from django.core.management.base import BaseCommand
from django.db import transaction

from antibioticsrct.models import Intervention
from antibioticsrct.models import InterventionContact


class Command(BaseCommand):
    help = '''Load interventions from practice allocations'''

    def add_arguments(self, parser):
        parser.add_argument('--allocations')
        parser.add_argument('--contacts')

    def handle(self, *args, **options):
        waves = [x[0] for x in Intervention.WAVE_CHOICES]
        methods = [x[0] for x in Intervention.METHOD_CHOICES]
        with transaction.atomic():
            if options['contacts']:
                InterventionContact.objects.all().delete()
                with open(options['contacts'], 'r') as f:
                    for contact in csv.DictReader(f):
                        InterventionContact.objects.create(
                            practice_id = contact['practice'],
                            name = contact['practice_name'],
                            address1 = contact['address1'],
                            address2 = contact['address2'],
                            address3 = contact['address3'],
                            address4 = contact['address4'],
                            postcode = contact['postcode'],
                            email = contact['merged emails'],
                            fax = contact['merged faxes'],
                        )
            if options['allocations']:
                # We don't delete allocations. They can not be changed
                # following the start of the RCT.
                with open(options['allocations'], 'r') as f:
                    for a in csv.DictReader(f):
                        if a['allocation'] != 'con':  # not a control
                            for wave in waves:
                                for method in methods:
                                    Intervention.objects.create(
                                        intervention=a['group_ab'],
                                        wave=wave,
                                        method=method,
                                        practice_id=a['practice_id'],
                                        # altered for A3 when wave generated:
                                        measure_id='ktt9_cephalosporins',
                                        contact_id=a['practice_id'],
                                    )
