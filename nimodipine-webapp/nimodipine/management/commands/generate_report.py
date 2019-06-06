import csv


from django.core.management.base import BaseCommand
from django.db import transaction
from nimodipine.models import Intervention
from nimodipine.models import InterventionContact


def numeric_truth(val):
    if val is True:
        return 1
    elif val is False:
        return 0
    elif val is None:
        return None


class Command(BaseCommand):
    help = '''Create CSV report for analysis'''

    def handle(self, *args, **options):
        needs_update = Intervention.objects.filter(
            receipt__isnull=True,
            sent=True
        )
        for intervention in needs_update:
            # This sets the receipt status of the email based on the mailgun logs
            intervention.set_receipt()


        f = open('intervention_report.csv', 'w')
        writer = csv.writer(f)
        header = ['practice_id', 'method', 'contactable', 'sent', 'delivery_success', 'hits']
        writer.writerow(header)
        for i in Intervention.objects.all():
            row = [
                i.practice_id,
                i.method,
                numeric_truth(i.contactable()),
                numeric_truth(i.sent),
                numeric_truth(i.receipt),
                i.hits
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
