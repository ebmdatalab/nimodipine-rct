from collections import OrderedDict

from django.test import TestCase
from .models import Intervention

class InterventionTestCase(TestCase):

    def test_url(self):
        intervention = Intervention.objects.create(
            intervention='A',
            wave='1',
            method='e',
            practice_id='P01234',
            measure_id='ktt9'
        )
        self.assertEqual(intervention.get_absolute_url(), '/e/1/P01234')
