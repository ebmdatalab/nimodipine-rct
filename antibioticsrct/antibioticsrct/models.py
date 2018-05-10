from datetime import date
import csv
import os
import re

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.urls import reverse

from anymail.signals import EventType

from common.utils import nhs_titlecase
from common.utils import encode
from common.utils import not_empty


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
    normalised_fax = models.CharField(max_length=25, null=True, blank=True)
    blacklisted = models.BooleanField(default=False)
    # "Did the message we sent give you new information about prescribing?"
    survey_response = models.NullBooleanField(default=None)

    @property
    def cased_name(self):
        return nhs_titlecase(self.name)

    def save(self, *args, **kwargs):
        fax_number = re.sub(r"[^0-9]", "", self.fax)
        if fax_number and re.search(r"[0-9]{8}", fax_number):
            if fax_number[:2] != '00':
                if fax_number[0] == '0':
                    fax_number = fax_number[1:]
                if fax_number[:2] == '44':
                    fax_number = '00' + fax_number
                else:
                    fax_number = '0044' + fax_number
        self.normalised_fax = fax_number
        super(InterventionContact, self).save(*args, **kwargs)


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
    sent = models.BooleanField(default=False)
    receipt = models.NullBooleanField(default=None)
    contact = models.ForeignKey(InterventionContact, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('method', 'wave', 'practice_id')
        ordering = ['created_date', 'intervention', 'method', 'wave', 'practice_id']

    def __str__(self):
        # Wondering hat get_method_display is? See
        # https://docs.djangoproject.com/en/2.0/ref/models/instances/#django.db.models.Model.get_FOO_display
        if self.method == 'e':
            recipient = self.contact.email
        elif self.method == 'f':
            recipient = self.contact.fax
        else:
            recipient = self.contact.name
        return "wave {}, intervention {}, method {}, to {}".format(
            self.wave,
            self.intervention,
            self.get_method_display().lower(),
            recipient)

    def contactable(self):
        if self.method == 'p':
            return True
        return not_empty(self.contact.email)

    def get_absolute_url(self):
        return reverse('views.intervention', args=[encode(self.method, self.wave), self.practice_id])

    def get_target_url(self):
        # add Google Analytics tracking
        querystring = "utm_source=rct1&utm_campaign=wave{}&utm_medium={}".format(
            self.wave,
            self.get_method_display().lower())
        target_url = "{}/practice/{}/?{}".format(
            settings.OP_HOST,
            self.practice_id,
            querystring)
        if int(self.wave) < 3:
            # In the first two waves, highlight the measure being
            # talked about.  See discussion starting here for why:
            # https://github.com/ebmdatalab/antibiotics-rct/issues/1#issuecomment-381990733
            target_url += '#' + self.measure_id
        return target_url

    def mail_logs(self):
        return MailLog.objects.filter(
            tags__contained_by=['antibioticsrct', "wave{}".format(self.wave)],
            recipient__iexact=self.contact.email)

    def set_receipt(self):
        if self.method == 'e':
            found = self.mail_logs()
            if found:
                if found.filter(event_type='delivered'):
                    self.receipt = True
                elif found.filter(event_type__in=['bounced', 'rejected']):
                    self.receipt = False
                self.save()

    def message_dir(self):
        location = os.path.join(
            settings.DATA_DIR,
            "wave" + self.wave,
            self.get_method_display().lower(),
            self.practice_id
        )
        os.makedirs(location, exist_ok=True)
        return location



# Copied from openprescribing, where this model is created via mailgun
# callbacks
class MailLog(models.Model):
    EVENT_TYPE_CHOICES = [
        (value, value)
        for name, value in vars(EventType).items()
        if not name.startswith('_')]
    metadata = JSONField(null=True, blank=True)
    recipient = models.CharField(max_length=254, db_index=True)
    tags = ArrayField(
        models.CharField(max_length=100, db_index=True),
        null=True
    )
    reject_reason = models.CharField(max_length=15, null=True, blank=True)
    event_type = models.CharField(
        max_length=15,
        choices=EVENT_TYPE_CHOICES,
        db_index=True)
    timestamp = models.DateTimeField(null=True, blank=True)
    # message = models.ForeignKey(EmailMessage, null=True, db_constraint=False)

    class Meta:
        db_table = 'frontend_maillog'
        managed = False


measure_data = {}

def get_measure_data():
    global measure_data
    if not measure_data:
        csv_path = os.path.join(settings.BASE_DIR, 'antibioticsrct', 'measures_advice.csv')
        with open(csv_path) as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                measure_data[row['short_title']] = row['compiled_explanation']
    return measure_data
