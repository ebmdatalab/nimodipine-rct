import io
import json
import logging
import os
import requests

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.urls import reverse

from google.cloud import bigquery
from google.api_core.exceptions import NotFound

from selenium import webdriver
from premailer import transform

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


def message_dir(intervention):
    location = os.path.join(
        settings.DATA_DIR,
        "wave" + intervention.wave,
        intervention.get_method_display().lower(),
        intervention.practice_id
    )
    os.makedirs(location, exist_ok=True)
    return location


def capture_html(url, target_path, width=None, height=None):
    driver = webdriver.PhantomJS()
    # it save service log file in same directory
    # if you want to have log file stored else where
    # initialize the webdriver.PhantomJS() as
    # driver = webdriver.PhantomJS(service_log_path='/var/log/phantomjs/ghostdriver.log')
    driver.set_script_timeout(30)
    if width and height:
        driver.set_window_size(width, height)
    driver.get(url)
    driver.save_screenshot(target_path)


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
            logger.info('Computing cost saving measures and stats for intervention A3')
            set_a3_metadata()
        interventions = Intervention.objects.filter(wave=options['wave'])
        if options['method']:
            interventions = interventions.filter(method=options['method'])
        if options['practice']:
            interventions = interventions.filter(practice_id=options['practice'])
        if options['sample']:
            interventions = interventions.order_by('?')[:options['sample']]
        for intervention in interventions:
            base = message_dir(intervention)
            contact = intervention.contact
            message_url = settings.URL_ROOT + reverse('views.intervention_message', args=[intervention.id])
            if intervention.method == 'e' and contact.email:  # email
                logger.info("Creating email at {}".format(base))
                response = requests.get(message_url)
                if response.status_code != requests.codes.ok:
                    raise Exception("bad response when trying to get {}".format(message_url))
                html = transform(response.text)
                metadata = {
                    'subject': 'Important information about your prescribing',
                    'from': 'seb.bacon@gmail.com',
                    'to': contact.email
                }
                with open(os.path.join(base, 'metadata.json'), 'w') as f:
                    json.dump(metadata, f)
                with open(os.path.join(base, 'email.html'), 'w') as f:
                    f.write(html)
                # XXX turn all images to be inline
            elif intervention.method == 'f' and contact.fax:  # fax
                logger.info("Creating fax at {}".format(base))
                capture_html(message_url, os.path.join(base, 'fax.png'))
                metadata = {
                    'to': contact.fax
                }
                with open(os.path.join(base, 'metadata.json'), 'w') as f:
                    json.dump(metadata, f)
            elif intervention.method == 'p' and contact.address1:  # printed letter
                # get screenshot
                logger.info("Creating postal letter at {}".format(base))
                capture_html(message_url, os.path.join(base, 'letter.png'))
            else:
                logger.warn("No valid contact info: %s", intervention)
