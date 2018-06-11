from email.utils import unquote
from unittest.mock import Mock
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
            ("(01234) 56789", "0044123456789"),
            ("123456789", "0044123456789"),
            ("#NA", ""),
            ("FALSE", ""),
            ("4412345678", "004412345678"),
            ("00442073726138", "00442073726138"),
            ("1", "1"),
        ]
        contact = InterventionContact.objects.first()
        for raw, expected in expectations:
            contact.fax = raw
            contact.save()
            self.assertEqual(contact.normalised_fax, expected)


class ReceiptTestCase(TestCase):
    fixtures = ['intervention_contacts', 'interventions', 'maillogs']

    def test_email_receipt(self):
        intervention = Intervention.objects.get(pk=1)
        self.assertEquals(intervention.receipt, None)
        intervention.set_receipt()
        self.assertTrue(intervention.receipt)

    def test_email_failure(self):
        intervention = Intervention.objects.get(pk=3)
        intervention.set_receipt()
        self.assertFalse(intervention.receipt)

    def test_email_other(self):
        intervention = Intervention.objects.get(pk=4)
        intervention.set_receipt()
        self.assertFalse(intervention.receipt)

    def test_email_no_maillog(self):
        intervention = Intervention.objects.get(pk=5)
        intervention.set_receipt()
        self.assertEquals(intervention.receipt, None)


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
            (3, 'intervention_a_2.html'),
            (4, 'intervention_a_3.html'),
            (5, 'intervention_b.html'),
            (6, 'intervention_b.html')
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
            'DestinationFax': '00441642260897',
            'Subject': 'message about your prescribing - 1',
            'Status': '0',
        }
        response = Client().post('/fax_receipt', data)
        intervention = Intervention.objects.get(pk=2)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(intervention.receipt)

    def test_fax_receipt_fail(self):
        data = {
            'DestinationFax': '00441642260897',
            'Subject': 'message about your prescribing - 1',
            'Status': '1',
        }
        response = Client().post('/fax_receipt', data)
        intervention = Intervention.objects.get(pk=2)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(intervention.receipt)

    def test_unknown_intervention_fax_receipt(self):
        data = {
            'DestinationFax': '12345',
            'Subject': 'message about your prescribing - 1',
            'Status': '0',
        }
        response = Client().post('/fax_receipt', data)
        Intervention.objects.get(pk=2)
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
    fixtures = ['intervention_contacts', 'interventions']
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
        msg_path = os.path.join(intervention_fixtures, 'wave1', 'email', 'A83050')
        with self.settings(DATA_DIR=intervention_fixtures):
            self.assertFalse(Intervention.objects.get(pk=1).sent)
            send_email_message(msg_path)
            self.assertTrue(Intervention.objects.get(pk=1).sent)
            self.assertEqual(len(outbox), 1)
            self.assertEqual(len(outbox[0].attachments), 1)
            self.assertEqual(outbox[0].to, ['simon.neil@nhs.net'])
            self.assertEqual(
                outbox[0].subject,
                'Information about your prescribing from OpenPrescribing.net')

    def test_email_dry_run(self):
        from antibioticsrct.management.commands.send_messages import send_email_message
        from django.core.mail import outbox
        intervention_fixtures = os.path.join(
            settings.BASE_DIR, 'antibioticsrct/fixtures/interventions/')
        msg_path = os.path.join(intervention_fixtures, 'wave1', 'email', 'A83050')
        with self.settings(DATA_DIR=intervention_fixtures):
            send_email_message(msg_path, dry_run=True)
            self.assertEqual(len(outbox), 0)


class FaxCommandTestCase(TestCase):
    fixtures = ['intervention_contacts', 'interventions']
    @patch('antibioticsrct.management.commands.send_messages.InterFAX')
    def test_send_fax(self, mock_interfax):
        from antibioticsrct.management.commands.send_messages import send_fax_message
        mock_interfax_instance = Mock()
        mock_interfax.return_value = mock_interfax_instance
        intervention_fixtures = os.path.join(
            settings.BASE_DIR, 'antibioticsrct/fixtures/interventions/')
        msg_path = os.path.join(intervention_fixtures, 'wave1', 'fax', 'A83050')
        with self.settings(DATA_DIR=intervention_fixtures):
            self.assertFalse(Intervention.objects.get(pk=2).sent)
            send_fax_message(msg_path)
            self.assertTrue(Intervention.objects.get(pk=2).sent)
            mock_interfax_instance.deliver.assert_called_with(
                '00441642260897',
                contact='Prescribing Lead',
                files=[os.path.join(msg_path, 'fax.pdf')],
                page_header='To: {To} From: {From} Pages: {TotalPages}',
                page_orientation='portrait',
                page_size='A4',
                reference='about your prescribing - 1',
                rendering='greyscale',
                reply_address=settings.FAX_FROM_EMAIL,
                resolution='fine')

    @patch('antibioticsrct.management.commands.send_messages.InterFAX')
    def test_fax_dry_run(self, mock_interfax):
        from antibioticsrct.management.commands.send_messages import send_fax_message
        mock_interfax_instance = Mock()
        mock_interfax.return_value = mock_interfax_instance
        intervention_fixtures = os.path.join(
            settings.BASE_DIR, 'antibioticsrct/fixtures/interventions/')
        msg_path = os.path.join(intervention_fixtures, 'wave1', 'fax', 'A83050')
        with self.settings(DATA_DIR=intervention_fixtures):
            send_fax_message(msg_path, dry_run=True)
            to = "j"
            mock_interfax_instance.deliver.assert_not_called()
