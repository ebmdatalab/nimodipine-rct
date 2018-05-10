import csv
import os

from antibioticsrct.models import Intervention
from antibioticsrct.models import InterventionContact
from antibioticsrct.management.commands.generate_wave import capture_html
from antibioticsrct.management.commands.send_messages import send_fax_message

from django.db.models import Q
from django.db import transaction
from django.conf import settings
from django.urls import reverse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def rewind_numbers():
    print("rewinding numbers")
    old_practice_data = csv.DictReader(
        open(os.path.join(BASE_DIR, "practices-pre-binleys.csv"), "r"))
    with transaction.atomic():
        for row in old_practice_data:
            contact = InterventionContact.objects.get(practice_id = row['code'])
            contact.fax = row['merged faxes']
            contact.save()


def set_receipts():
    print("setting receipts")
    logs = csv.DictReader(
        open(os.path.join(BASE_DIR, "transactions.csv"), "r"))
    with transaction.atomic():
        errors = []
        for line in logs:
            recipient = line['DestinationFax'].strip()
            status = line['Status']
            interventions = Intervention.objects.filter(
                contact__normalised_fax=recipient, wave='1', method='f')
            if interventions.count() > 0:
                if status == '0':
                    interventions.update(receipt=True)
                else:
                    interventions.update(receipt=False)
            else:
                errors.append(recipient)
        if errors:
            print("\n".join(errors))
            raise



def set_newer_numbers():
    print("setting newer numbers")
    faxes = {}
    new_practice_data = csv.DictReader(
        open(os.path.join(BASE_DIR, "practices-post-binleys.csv"), "r"))
    for row in new_practice_data:
        faxes[row['practice']] = row['merged faxes']

    # find interventions that haven't been sent, or have been sent
    # unsuccessfully
    query = Q(wave='1', method='f') & (
        Q(receipt__isnull=True) | Q(receipt=False)
    )
    interventions = Intervention.objects.filter(query)
    with transaction.atomic():
        # set their fax number to latest available
        for intervention in interventions:
            new_fax = faxes.get(intervention.practice_id, None)
            if new_fax:
                print(intervention)
                intervention.fax = new_fax
                # set their 'sent' flag to false so we can resend them
                intervention.sent = False
                intervention.save()


def generate_and_send():
    print("generating and sending")
    interventions = Intervention.objects.filter(
        sent=False, contact__normalised_fax__isnull=False)
    for intervention in interventions[0:1]:
        print(intervention)
        message_url = settings.URL_ROOT + reverse('views.intervention_message', args=[intervention.id])
        base = intervention.message_dir()
        print("Creating fax at {} via URL {}".format(base, message_url))
        capture_html(message_url, os.path.join(base, 'fax.pdf'))
        send_fax_message(base, dry_run=True)

def run():
    rewind_numbers()
    set_receipts()
    set_newer_numbers()
    generate_and_send()
