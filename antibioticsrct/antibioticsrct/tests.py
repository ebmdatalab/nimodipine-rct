from unittest.mock import patch
import os

from django.conf import settings
from django.core.management import call_command
from django.test import Client
from django.test import TestCase

from antibioticsrct.models import Intervention


class ModelTestCase(TestCase):
    fixtures = ['intervention_contacts', 'interventions']

    def test_url_generation(self):
        intervention = Intervention.objects.get(pk=1)
        self.assertEqual(intervention.get_absolute_url(), '/e/1/A83050')


class BigQueryIntegrationTestCase(TestCase):
    fixtures = ['intervention_contacts', 'interventions']

    def test_metadata_setting(self):
        from antibioticsrct.management.commands.generate_wave import set_a3_metadata
        set_a3_metadata(allocation_table='test_allocated_practices')
        a3_intervention = Intervention.objects.get(pk=3)
        self.assertTrue(a3_intervention.metadata)
        self.assertNotEqual(a3_intervention.measure_id, 'ktt9')


class ViewTestCase(TestCase):
    fixtures = ['intervention_contacts', 'interventions']
    def test_target_url_redirect(self):
        expected = ('https://openprescribing.net/practice/A83050/'
                    '?utm_source=rct1&utm_campaign=wave1&utm_medium=email'
                    '#ktt9')
        client = Client()
        response = client.get('/e/1/A83050/')
        self.assertRedirects(response, expected, fetch_redirect_response=False)

    def test_click_count(self):
        Client().get('/e/1/A83050/')
        intervention = Intervention.objects.get(pk=1)
        self.assertEqual(intervention.hits, 1)

    @patch('antibioticsrct.views.grab_image')
    def test_intervention_message_template(self, mock_image):
        img_str = '*** base64 encoded image ***'
        mock_image.return_value = img_str
        expectations = [
            (1, 'intervention_a_1.html'),
            (2, 'intervention_a_2.html'),
            (3, 'intervention_a_3.html'),
            (4, 'intervention_b.html'),
            (5, 'intervention_b.html')
        ]
        for pk, template in expectations:
            intervention = Intervention.objects.get(pk=pk)
            response = Client().get("/msg/{}".format(pk))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, template)
            self.assertEquals(response.context['intervention'], intervention)
            self.assertEquals(response.context['encoded_image'], img_str)


class CommandsTestCase(TestCase):
    def test_create_interventions(self):
        allocations = os.path.join(
            settings.BASE_DIR, 'antibioticsrct/fixtures/allocations.csv')
        contacts = os.path.join(
            settings.BASE_DIR, 'antibioticsrct/fixtures/contacts.csv')
        args = []
        opts = {'allocations': allocations, 'contacts': contacts}
        call_command('create_interventions', *args, **opts)

        # 3 waves of email, fax, and post for 2 non-control practices
        self.assertEqual(Intervention.objects.count(), 18)
        # Final email, fax, and post for 2 non-control practices
        self.assertEqual(len(Intervention.objects.filter(wave='3')), 6)
        # Final wave of email, fax and post for the 1 practice assigned intervention A
        ppi_interventions = Intervention.objects.filter(measure_id='ppi')
        self.assertTrue(all([x.wave == '3' for x in ppi_interventions]))
        self.assertEqual(len(ppi_interventions), 3)

        # Check contact details
        self.assertEqual(ppi_interventions.first().contact.name, "THE SALTSCAR SURGERY")
