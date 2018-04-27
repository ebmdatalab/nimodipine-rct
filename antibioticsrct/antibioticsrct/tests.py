from email.utils import unquote
from unittest.mock import patch
import os

from django.conf import settings
from django.core.management import call_command
from django.test import Client
from django.test import TestCase

from antibioticsrct.models import Intervention
from antibioticsrct.models import InterventionContact


class ModelTestCase(TestCase):
    fixtures = ['intervention_contacts', 'interventions']

    def test_url_generation(self):
        intervention = Intervention.objects.get(pk=1)
        self.assertEqual(intervention.get_absolute_url(), '/a/A83050')

    def test_normalised_fax(self):
        expectations = [
            ("(01234) 56789", "44123456789"),
            ("#NA", ""),
            ("FALSE", ""),
            ("4412345678", "4412345678"),
            ("1", "1"),
        ]
        contact = InterventionContact.objects.first()
        for raw, expected in expectations:
            contact.fax = raw
            contact.save()
            self.assertEqual(contact.normalised_fax, expected)


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
    def test_target_url_questionnaire(self):
        client = Client()
        response = client.get('/a/A83050')
        self.assertTemplateUsed(response, 'questionnaire.html')

    def test_target_url_questionnaire_post(self):
        expected = ('{}/practice/A83050/'
                    '?utm_source=rct1&utm_campaign=wave1&utm_medium=email'
                    '#ktt9_antibiotics'.format(settings.OP_HOST))
        client = Client()
        response = client.post('/a/A83050', {'survey_response':'Yes'})
        self.assertRedirects(response, expected, fetch_redirect_response=False)
        intervention = Intervention.objects.get(practice_id='A83050', method='e', wave='1')
        self.assertTrue(intervention.contact.survey_response)
        self.assertEquals(intervention.hits, 0)  # don't increment the counter on POSTs

    def test_target_url_redirect_when_already_visited(self):
        expected = ('{}/practice/A83050/'
                    '?utm_source=rct1&utm_campaign=wave2&utm_medium=email'
                    '#ktt9_antibiotics'.format(settings.OP_HOST))
        client = Client()
        response = client.get('/b/A83050')
        self.assertRedirects(response, expected, fetch_redirect_response=False)

    def test_click_count(self):
        Client().get('/a/A83050/')
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

    def test_fax_receipt_success(self):
        data = {
            'sender': 'seb',
            'recipient': 'kim',
            'subject': 'Successful transmission to 441642260897. Re: message about your prescribing - 1',
            'strippted-text': 'Some stuff'
        }
        response = Client().post('/fax_receipt', data)
        intervention = Intervention.objects.get(pk=6)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(intervention.receipt)

    def test_fax_receipt_fail(self):
        data = {
            'sender': 'seb',
            'recipient': 'kim',
            'subject': 'Unuccessful transmission to 441642260897. Re: message about your prescribing - 1',
            'strippted-text': 'Some stuff'
        }
        response = Client().post('/fax_receipt', data)
        intervention = Intervention.objects.get(pk=6)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(intervention.receipt)

    def test_unknown_intervention_fax_receipt(self):
        data = {
            'sender': 'seb',
            'recipient': 'kim',
            'subject': 'Unuccessful transmission to 0123456. Re: message about your prescribing - 1',
            'strippted-text': 'Some stuff'
        }
        response = Client().post('/fax_receipt', data)
        Intervention.objects.get(pk=6)
        self.assertEqual(response.status_code, 404)


class InterventionCommandTestCase(TestCase):
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

        # Check contact details
        self.assertEqual(Intervention.objects.first().contact.name, "THE SALTSCAR SURGERY")


class EmailCommandTestCase(TestCase):
    def test_email_from_html(self):
        from antibioticsrct.management.commands.send_messages import inline_images
        from django.core.mail import EmailMultiAlternatives

        msg = EmailMultiAlternatives(subject="foo")
        html = 'some <b>html</b> and stuff <img src="data:image/png;base64,cafe"> ting'
        msg = inline_images(msg, html)
        attachment = msg.attachments[0]
        self.assertEqual(attachment.get_payload(), 'cafe')
        cid = unquote(attachment.get('content-id'))
        self.assertIn('<img src="cid:{}">'.format(cid), msg.alternatives[0][0])

    def test_send_email(self):
        from antibioticsrct.management.commands.send_messages import send_email_message
        from django.core.mail import outbox
        intervention_fixtures = os.path.join(
            settings.BASE_DIR, 'antibioticsrct/fixtures/interventions/')
        msg_path = os.path.join(intervention_fixtures, 'wave1', 'email', 'D83017')
        with self.settings(DATA_DIR=intervention_fixtures):
            send_email_message(msg_path)
            self.assertEqual(len(outbox), 1)
            self.assertEqual(len(outbox[0].attachments), 1)
            self.assertEqual(outbox[0].to, ['seb.bacon+test@gmail.com'])
            self.assertEqual(outbox[0].subject, 'Important information about your prescribing')
