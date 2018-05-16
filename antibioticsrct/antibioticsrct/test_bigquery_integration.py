from django.test import TestCase

from antibioticsrct.models import Intervention


class BigQueryIntegrationTestCase(TestCase):
    fixtures = ['intervention_contacts', 'interventions']
    def test_metadata_setting(self):
        from antibioticsrct.management.commands.generate_wave import set_a3_metadata
        set_a3_metadata(allocation_table='test_allocated_practices')
        a3_intervention = Intervention.objects.get(pk=4)
        self.assertTrue(a3_intervention.metadata)
        self.assertNotEqual(a3_intervention.measure_id, 'ktt9')
