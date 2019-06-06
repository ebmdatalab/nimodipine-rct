import csv


from django.core.management.base import BaseCommand
from django.db import transaction

from nimodipine.models import Intervention
from nimodipine.models import InterventionContact


class Command(BaseCommand):
    help = '''Load interventions from practice contact list'''

    def add_arguments(self, parser):
        parser.add_argument('--contacts', required=True)

    def handle(self, *args, **options):
        methods = [x[0] for x in Intervention.METHOD_CHOICES]
        with transaction.atomic():
            if options['contacts']:
                InterventionContact.objects.all().delete()
                with open(options['contacts'], 'r') as f:
                    for contact in csv.DictReader(f):
                        InterventionContact.objects.create(
                            practice_id=contact['practice'],
                            name=contact['practice_name'],
                            address1=contact['address1'],
                            address2=contact['address2'],
                            address3=contact['address3'],
                            address4=contact['address4'],
                            postcode=contact['postcode'],
                            email=contact['merged emails'],
                            fax=contact['merged faxes'],
                        )
                        for method in methods:
                            Intervention.objects.create(
                                method=method,
                                practice_id=contact['practice'],
                                contact_id=contact['practice'],
                            )
