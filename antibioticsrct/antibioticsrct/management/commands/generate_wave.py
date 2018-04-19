import io
import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from google.cloud import bigquery
from google.api_core.exceptions import NotFound

from antibioticsrct.models import Intervention
from antibioticsrct.models import InterventionContact

logger = logging.getLogger(__name__)


def create_practices_table_in_bq(client, interventions, allocation_table):
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

def set_a3_metadata(allocation_table='allocated_practices'):
    interventions = Intervention.objects.filter(
        wave='3',
        intervention='A'
    )
    client = bigquery.Client()
    create_practices_table_in_bq(client, interventions, allocation_table)
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
        intervention = interventions.get(practice_id=row[0])
        intervention.measure_id = metadata['measure']
        intervention.metadata = metadata
        intervention.save()


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

    def handle(self, *args, **options):
        if options['wave'] == '3':
            logger.info('Selecting measure for intervention A3')
            set_a3_metadata(options['practices'])
        interventions = Intervention.objects.filter(wave=options['wave'])
        if options['sample']:
            interventions = interventions.order_by('?')[options['sample']]
        for intervention in interventions:
            if intervention.method == 'e':  # email
                # generate  HTML
                # run through premail
                # save to appropriate location
                # metadata: Subject, To, From
                pass
            elif intervention.method == 'f':  # fax
                # get screenshot
                # save to appropriate location
                # metadata: fax number
                pass
            else:  # printed letter
                # get screenshot
                # save to appropriate location
                # metadata: name ("prescribing lead"), address
                pass
