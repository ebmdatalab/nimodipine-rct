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

from antibioticsrct.models import Intervention
from antibioticsrct.models import InterventionContact

logger = logging.getLogger(__name__)


def create_practices_table_in_bq(client, allocation_table):
    interventions = a3_interventions()
    dataset = client.get_dataset(client.dataset('tmp_eu'))
    schema = [
        bigquery.SchemaField('practice', 'STRING', mode='REQUIRED'),
    ]
    table_ref = dataset.table(allocation_table)
    try:
        client.delete_table(table_ref)
    except NotFound:
        pass
    mock_csv = io.BytesIO(
        ("\n".join(
            list(interventions.values_list('practice_id', flat=True)))
        ).encode('ascii'))
    job_config = bigquery.LoadJobConfig()
    job_config.source_format = 'CSV'
    job_config.skip_leading_rows = 0
    job_config.schema = schema
    job = client.load_table_from_file(
        mock_csv,
        table_ref,
        location='EU',
        job_config=job_config)
    job.result()  # Waits for table load to complete.
    assert job.state == 'DONE'


def a3_interventions():
    return Intervention.objects.filter(
        wave='3',
        intervention='A')


def set_a3_metadata(allocation_table='allocated_practices'):
    client = bigquery.Client()
    create_practices_table_in_bq(client, allocation_table)
    query_str = open(
        os.path.join(
            settings.BASE_DIR,
            'antibioticsrct', 'management',
            'commands', 'a3_metadata.sql'),
        'r').read().format(allocation_table=allocation_table)
    query_job = client.query(
        query_str,
        location='EU')
    timeout = 30  # in seconds
    iterator = query_job.result(timeout=timeout)
    for row in iterator:
        metadata = dict(row.items())
        interventions = a3_interventions().filter(practice_id=row[0])
        interventions.update(
            measure_id=metadata['measure'],
            metadata=metadata)


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


def combine_letters(wave):
    wave_dir = os.path.join(settings.DATA_DIR, "wave" + wave)
    inputs = find('letter.pdf', wave_dir)
    subprocess.check_call([
        "gs", "-q", "-sPAPERSIZE=letter", "-dNOPAUSE",
        "-dBATCH", "-sDEVICE=pdfwrite",
        "-sOutputFile={}/combined_letters.pdf".format(wave_dir)] + inputs)


def not_empty(cell):
    cell = cell.strip()
    if cell and cell not in ['#N/A', 'FALSE']:
        return True
    return False


class Command(BaseCommand):
    help = '''Load interventions from practice allocations'''

    def add_arguments(self, parser):
        parser.add_argument('--wave', type=str)
        parser.add_argument('--practices', type=str,
                            help='CSV of allocated practices')
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
        if options['wave'] == '3':
            logger.info('Computing customised measures and stats for intervention A3')
            set_a3_metadata()
        interventions = Intervention.objects.filter(
            contact__blacklisted=False, wave=options['wave'])
        if options['method']:
            interventions = interventions.filter(method=options['method'])
        if options['practice']:
            interventions = interventions.filter(practice_id=options['practice'])
        if options['sample']:
            interventions = interventions.order_by('?')[:options['sample']]
        for intervention in interventions:
            base = intervention.message_dir()
            contact = intervention.contact
            metadata = {'wave': options['wave']}
            message_url = settings.URL_ROOT + reverse('views.intervention_message', args=[intervention.id])
            if intervention.method == 'e' and not_empty(contact.email):  # email
                logger.info("Creating email at {}".format(base))
                response = requests.get(message_url)
                if response.status_code != requests.codes.ok:
                    raise Exception("bad response when trying to get {}".format(message_url))
                html = Premailer(response.text, cssutils_logging_level=logging.ERROR).transform()
                metadata.update({
                    'subject': 'Important information about your prescribing',
                    'from': 'seb.bacon@gmail.com',
                    'to': contact.email
                })
                with open(os.path.join(base, 'metadata.json'), 'w') as f:
                    json.dump(metadata, f)
                with open(os.path.join(base, 'email.html'), 'w') as f:
                    f.write(html)
            elif intervention.method == 'f' and not_empty(contact.fax):  # fax
                logger.info("Creating fax at {}".format(base))
                capture_html(message_url, os.path.join(base, 'fax.pdf'))
                metadata.update({
                    'to': contact.normalised_fax
                })
                with open(os.path.join(base, 'metadata.json'), 'w') as f:
                    json.dump(metadata, f)
            elif intervention.method == 'p' and contact.address1:  # printed letter
                # get screenshot
                logger.info("Creating postal letter at {}".format(base))
                capture_html(message_url, os.path.join(base, 'letter.pdf'))
            else:
                logger.warn("No valid contact info: %s", intervention)
        combine_letters(options['wave'])
