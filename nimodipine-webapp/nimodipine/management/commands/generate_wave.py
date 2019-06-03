import io
import json
import logging
import fnmatch
import os
import requests
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.urls import reverse

from google.cloud import bigquery
from google.api_core.exceptions import NotFound

from premailer import Premailer

from nimodipine.models import Intervention
from nimodipine.models import InterventionContact
from common.utils import not_empty


logger = logging.getLogger(__name__)


def capture_html(url, target_path):
    cmd = '{cmd} "{url}" {target_path}'
    cmd = cmd.format(
            cmd=settings.PRINT_CMD,
            url=url,
            target_path=target_path,
    )
    subprocess.check_output(cmd, shell=True)


def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result


def combine_letters():
    """Combine all the letters into 1 PDF to make it easier to print

    """
    inputs = find('letter.pdf', settings.DATA_DIR)
    subprocess.check_call([
        "gs", "-q", "-sPAPERSIZE=letter", "-dNOPAUSE",
        "-dBATCH", "-sDEVICE=pdfwrite",
        "-sOutputFile={}/combined_letters.pdf".format(settings.DATA_DIR)] + inputs)


def count_expected():
    """Check expected number of interventions generated against number on
    filesystem
    """
    generated_count = 0
    not_generated = []
    count = Intervention.objects.count()
    for intervention in Intervention.objects.all():
        if intervention.is_generated():
            generated_count += 1
        else:
            not_generated.append(intervention)
    print("{}% of {} generated".format(
        (generated_count/count) * 100, count))
    if count < generated_count:
        print("Missing:")
        print(not_generated)


class Command(BaseCommand):
    help = '''Load interventions from practice allocations'''
    def add_arguments(self, parser):
        parser.add_argument('--sample',
                            type=int,
                            default=0,
                            help='If set, generate messages for only N practices')
        parser.add_argument('--method',
                            type=str,
                            default=None,
                            help='If set, generate messages for only this method (e, p, or f)')
        parser.add_argument('--practice',
                            type=str,
                            default=None,
                            help='If set, generate messages for only this practice')


    def handle(self, *args, **options):
        interventions = Intervention.objects.filter(contact__blacklisted=False)
        if options['method']:
            interventions = interventions.filter(method=options['method'])
        if options['practice']:
            interventions = interventions.filter(practice_id=options['practice'])
        if options['sample']:
            interventions = interventions.order_by('?')
        saved = 0
        for intervention in interventions:
            if options['sample'] and saved >= options['sample']:
                break
            if intervention.is_generated():
                logger.info("Skipping generating %s as already done", intervention)
                continue
            contact = intervention.contact
            message_url = settings.URL_ROOT + reverse(
                'views.intervention_message', args=[intervention.id])
            destination = intervention.message_path()
            if intervention.method == 'e' and not_empty(contact.email):  # email
                logger.info("Creating email at {} via URL {}".format(destination, message_url))
                response = requests.get(message_url)
                if response.status_code != requests.codes.ok:
                    raise Exception("bad response when trying to get {}".format(message_url))
                html = Premailer(response.text, cssutils_logging_level=logging.ERROR).transform()
                with open(destination, 'w') as f:
                    f.write(html)
                intervention.generated = True
                intervention.save()
                saved += 1
            elif intervention.method == 'f' and not_empty(contact.normalised_fax):  # fax
                logger.info("Creating fax at {} via URL {}".format(destination, message_url))
                capture_html(message_url, destination)
                intervention.generated = True
                intervention.save()
                saved += 1
            elif intervention.method == 'p' and contact.address1:  # printed letter
                base = intervention.message_dir()
                logger.info("Creating postal letter at {}".format(base))
                capture_html(message_url, destination)
                intervention.generated = True
                intervention.save()
                saved += 1
            else:
                logger.info("No valid contact info: %s", intervention)
        combine_letters()
        count_expected()
