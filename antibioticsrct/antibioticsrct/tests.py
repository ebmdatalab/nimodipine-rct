from collections import OrderedDict

from django.test import Client
from django.test import TestCase
from antibioticsrct.models import Intervention

class ModelTestCase(TestCase):
    fixtures = ['interventions']

    def test_url_generation(self):
        intervention = Intervention.objects.get(pk=1)
        self.assertEqual(intervention.get_absolute_url(), '/e/1/P01234')

class ViewTestCase(TestCase):
    fixtures = ['interventions']
    def test_target_url_redirect(self):
        expected = ('https://openprescribing.net/practice/P01234/'
                    '?utm_source=rct1&utm_campaign=wave1&utm_medium=email'
                    '#ktt9')
        client = Client()
        response = client.get('/e/1/P01234/')
        self.assertRedirects(response, expected, fetch_redirect_response=False)

    def test_click_count(self):
        Client().get('/e/1/P01234/')
        intervention = Intervention.objects.get(pk=1)
        self.assertEqual(intervention.hits, 1)
