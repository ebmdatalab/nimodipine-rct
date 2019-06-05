from email.utils import unquote
from unittest.mock import Mock
from unittest.mock import patch
import os

from django.conf import settings
from django.core.management import call_command
from django.test import Client
from django.test import TestCase

from nimodipine.models import Intervention
from nimodipine.models import InterventionContact


class ModelTestCase(TestCase):
    fixtures = ['intervention_contacts', 'interventions']

    def test_url_generation(self):
        intervention = Intervention.objects.get(pk=1)
        self.assertEqual(intervention.get_absolute_url(), '/e/A83050')

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
        response = client.get('/p/A81025')  # No questionnaire hits in any wave
        self.assertTemplateUsed(response, 'questionnaire.html')

    def test_target_url_questionnaire_post(self):
        """Check that when we fill out a questionnaire for an intervention for
        a practice which has never previously had any vists, we
        redirect to the practice page.
        """
        expected = ('{}/measure/nimodipine/practice/A81025/'
                    '?utm_source=nimodipine&utm_medium=post'.format(settings.OP_HOST))
        client = Client()
        response = client.post('/p/A81025', {'survey_response': 'Yes'})
        self.assertRedirects(response, expected, fetch_redirect_response=False)
        intervention = Intervention.objects.get(
            practice_id='A81025', method='p')
        self.assertTrue(intervention.contact.survey_response)
        # don't increment the counter on POSTs
        self.assertEquals(intervention.hits, 0)

    def test_target_url_redirect_when_already_visited(self):
        """This is a request for an intervention in wave *2*.  In the
        fixtures, this wave is associated with someone having
        previously visited the questionnaire page."

        """
        expected = ('{}/measure/nimodipine/practice/A83050/'
                    '?utm_source=nimodipine&utm_medium=post'.format(settings.OP_HOST))
        client = Client()
        response = client.get('/p/A83050')
        self.assertRedirects(response, expected, fetch_redirect_response=False)

    def test_click_count(self):
        Client().get('/e/A83050/')
        intervention = Intervention.objects.get(pk=1)
        self.assertEqual(intervention.hits, 1)


    def test_fax_receipt_success(self):
        data = {
            'DestinationFax': '00441642260897',
            'Subject': 'message about your prescribing',
            'Status': '0',
        }
        response = Client().post('/fax_receipt', data)
        intervention = Intervention.objects.get(pk=2)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(intervention.receipt)

    def test_fax_receipt_fail(self):
        data = {
            'DestinationFax': '00441642260897',
            'Subject': 'message about your prescribing',
            'Status': '1',
        }
        response = Client().post('/fax_receipt', data)
        intervention = Intervention.objects.get(pk=2)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(intervention.receipt)

    def test_unknown_intervention_fax_receipt(self):
        data = {
            'DestinationFax': '12345',
            'Subject': 'message about your prescribing',
            'Status': '0',
        }
        response = Client().post('/fax_receipt', data)
        Intervention.objects.get(pk=2)
        self.assertEqual(response.status_code, 404)


class InterventionCommandTestCase(TestCase):
    def test_create_interventions(self):
        allocations = os.path.join(
            settings.BASE_DIR, 'nimodipine/fixtures/allocations.csv')
        contacts = os.path.join(
            settings.BASE_DIR, 'nimodipine/fixtures/contacts.csv')
        args = []
        opts = {'allocations': allocations, 'contacts': contacts}
        call_command('create_interventions', *args, **opts)

        self.assertEqual(Intervention.objects.count(), 6)

        # Check contact details
        self.assertEqual(Intervention.objects.first().contact.name, "THE SALTSCAR SURGERY")


class WaveGenerationCommandTestCase(TestCase):
    fixtures = ['intervention_contacts', 'interventions']
    @patch('nimodipine.management.commands.generate_wave.requests')
    def test_generate_wave(self, mock_request):
        args = []
        opts = {'method': 'e'}
        mock_request.get = Client().get
        mock_request.codes.ok = 200
        call_command('generate_wave', *args, **opts)
        intervention = Intervention.objects.first()
        path = intervention.message_path()
        expected = 'You can learn more about how your prescription rates for nimodipine compare to other practices at <a href="http://op2.org.uk/e/{practice_id}">op2.org.uk/e/{practice_id}</a>'.format(practice_id=intervention.practice_id)
        email = open(path, "r").read()
        self.assertIn(expected, email)


class EmailCommandTestCase(TestCase):
    fixtures = ['intervention_contacts', 'interventions']
    def test_email_from_html(self):
        from nimodipine.management.commands.send_messages import inline_images
        from django.core.mail import EmailMultiAlternatives

        msg = EmailMultiAlternatives(subject="foo")
        html = 'some <b>html</b> and stuff <img src="data:image/png;base64,cafe"> ting'
        msg = inline_images(msg, html)
        attachment = msg.attachments[0]
        self.assertEqual(attachment.get_payload(), 'cafe')
        cid = unquote(attachment.get('content-id'))
        self.assertIn('<img src="cid:{}">'.format(cid), msg.alternatives[0][0])

    def test_send_email(self):
        from nimodipine.management.commands.send_messages import send_email_message
        from django.core.mail import outbox
        intervention_fixtures = os.path.join(
            settings.BASE_DIR, 'nimodipine/fixtures/interventions/')
        msg_path = os.path.join(intervention_fixtures, 'email', 'A83050')
        with self.settings(DATA_DIR=intervention_fixtures):
            self.assertFalse(Intervention.objects.get(pk=1).sent)
            send_email_message(msg_path)
            self.assertTrue(Intervention.objects.get(pk=1).sent)
            self.assertEqual(len(outbox), 1)
            self.assertEqual(len(outbox[0].attachments), 1)
            self.assertEqual(outbox[0].to, ['simon.neil@nhs.net'])
            self.assertEqual(
                outbox[0].subject,
                'Information about your nimodipine prescribing from OpenPrescribing.net')

    def test_email_dry_run(self):
        from nimodipine.management.commands.send_messages import send_email_message
        from django.core.mail import outbox
        intervention_fixtures = os.path.join(
            settings.BASE_DIR, 'nimodipine/fixtures/interventions/')
        msg_path = os.path.join(intervention_fixtures, 'email', 'A83050')
        with self.settings(DATA_DIR=intervention_fixtures):
            send_email_message(msg_path, dry_run=True)
            self.assertEqual(len(outbox), 0)


class FaxCommandTestCase(TestCase):
    fixtures = ['intervention_contacts', 'interventions']
    @patch('nimodipine.management.commands.send_messages.InterFAX')
    def test_send_fax(self, mock_interfax):
        from nimodipine.management.commands.send_messages import send_fax_message
        mock_interfax_instance = Mock()
        mock_interfax.return_value = mock_interfax_instance
        intervention_fixtures = os.path.join(
            settings.BASE_DIR, 'nimodipine/fixtures/interventions/')
        msg_path = os.path.join(intervention_fixtures, 'fax', 'A83050')
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
                reference='about your nimodipine prescribing',
                rendering='greyscale',
                reply_address=settings.FAX_FROM_EMAIL,
                resolution='fine')

    @patch('nimodipine.management.commands.send_messages.InterFAX')
    def test_fax_dry_run(self, mock_interfax):
        from nimodipine.management.commands.send_messages import send_fax_message
        mock_interfax_instance = Mock()
        mock_interfax.return_value = mock_interfax_instance
        intervention_fixtures = os.path.join(
            settings.BASE_DIR, 'nimodipine/fixtures/interventions/')
        msg_path = os.path.join(intervention_fixtures, 'fax', 'A83050')
        with self.settings(DATA_DIR=intervention_fixtures):
            send_fax_message(msg_path, dry_run=True)
            to = "j"
            mock_interfax_instance.deliver.assert_not_called()
