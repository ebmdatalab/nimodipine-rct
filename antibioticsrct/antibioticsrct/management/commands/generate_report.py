import csv


from django.core.management.base import BaseCommand
from django.db import transaction
from antibioticsrct.models import Intervention
from antibioticsrct.models import InterventionContact


def numeric_truth(val):
    if val is True:
        return 1
    elif val is False:
        return 0
    elif val is None:
        return None


class Command(BaseCommand):
    help = '''Create CSV report for analysis'''

    def add_arguments(self, parser):
        parser.add_argument('--wave', type=str)

    def handle(self, *args, **options):
        needs_update = Intervention.objects.filter(
            receipt__isnull=True,
            sent=True
        )
        if options['wave']:
            needs_update = needs_update.filter(wave=options['wave'])
        for intervention in needs_update:
            intervention.set_receipt()


        f = open('intervention_report.csv', 'w')
        writer = csv.writer(f)
        header = ['practice_id', 'wave', 'method', 'contactable', 'sent', 'delivery_success']
        writer.writerow(header)
        for i in Intervention.objects.all():
            row = [
                i.practice_id,
                i.wave,
                i.method,
                numeric_truth(i.contactable()),
                numeric_truth(i.sent),
                numeric_truth(i.receipt)
            ]
            writer.writerow(row)
        print("Intervention report written to {}".format(f.name))

        f = open('questionnaire_report.csv', 'w')
        writer = csv.writer(f)
        header = ['practice_id', 'answer']
        writer.writerow(header)
        for i in InterventionContact.objects.all():
            row = [
                i.practice_id,
                numeric_truth(i.survey_response)
            ]
            writer.writerow(row)
        print("Questionnaire report written to {}".format(f.name))
