from datetime import date
import os

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.urls import reverse

from common.utils import nhs_titlecase

OP_HOST = "https://openprescribing.net"


class InterventionContact(models.Model):
    practice_id = models.CharField(max_length=6, primary_key=True)
    name = models.CharField(max_length=200)
    address1 = models.CharField(max_length=100, null=True, blank=True)
    address2 = models.CharField(max_length=100, null=True, blank=True)
    address3 = models.CharField(max_length=100, null=True, blank=True)
    address4 = models.CharField(max_length=100, null=True, blank=True)
    postcode = models.CharField(max_length=9, null=True, blank=True)
    email = models.EmailField(max_length=200, null=True, blank=True)
    fax = models.CharField(max_length=25, null=True, blank=True)

    @property
    def cased_name(self):
        return nhs_titlecase(self.name)


class Intervention(models.Model):
    INTERVENTION_CHOICES = (
        ('A', 'A (with content changes)'),
        ('B', 'B (without content changes)'),
    )
    WAVE_CHOICES = (
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
    )
    METHOD_CHOICES = (
        ('e', 'Email'),
        ('p', 'Post'),
        ('f', 'Fax'),
    )
    created_date = models.DateField(default=date.today)
    intervention = models.CharField(max_length=1, choices=INTERVENTION_CHOICES)
    wave = models.CharField(max_length=1, choices=WAVE_CHOICES)
    method = models.CharField(max_length=1, choices=METHOD_CHOICES)
    practice_id = models.CharField(max_length=6)
    measure_id = models.CharField(max_length=40, default='ktt9_cephalosporins')
    metadata = JSONField(null=True, blank=True)
    hits = models.IntegerField(default=0)
    contact = models.ForeignKey(InterventionContact, on_delete=models.CASCADE)

    def __str__(self):
        return "Intervention {}: wave {}, intervention {}, method {}".format(
            self.pk,
            self.wave,
            self.intervention,
            self.get_method_display().lower())

    def get_absolute_url(self):
        return reverse('views.intervention', args=[self.method, self.wave, self.practice_id])

    def get_target_url(self):
        # XXX Maybe we should jump to https://openprescribing.net/measure/saba/ccg/11X/?
        querystring = "utm_source=rct1&utm_campaign=wave{}&utm_medium={}".format(
            self.wave,
            self.get_method_display().lower()
        )
        return "{}/practice/{}/?{}#{}".format(
            OP_HOST,
            self.practice_id,
            querystring,
            self.measure_id)

    def message_dir(self):
        location = os.path.join(
            settings.DATA_DIR,
            "wave" + self.wave,
            self.get_method_display().lower(),
            self.practice_id
        )
        os.makedirs(location, exist_ok=True)
        return location

    class Meta:
        unique_together = ('method', 'wave', 'practice_id')
        ordering = ['created_date', 'intervention', 'method', 'wave', 'practice_id']


class MeasureWording(models.Model):
    pass
    # If it's intervention A and it's ktt9_cephalosporins, the content is in the template
    # Otherwise, it's one of 8 cost-saving measures:
    #ace.json
    #arb.json
    #desogestrel.json
    #keppra.json
    #lyrica.json
    #ppi.json
    #quetiapine.json
    #statins.json
    # And it should say something like "For example, here’s how your practice compares to other practices for prescriptions of high-cost proton-pump inhibitors (PPIs). You could have saved £630.80 over the last 6 months by prescribing generic-brand PPIs instead."
    # If it's intervention B the content is in the template.
