from datetime import date

from django.db import models
from django.urls import reverse

OP_HOST = "https://openprescribing.net"

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
    measure_id = models.CharField(max_length=40)
    hits = models.IntegerField(default=0)

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
