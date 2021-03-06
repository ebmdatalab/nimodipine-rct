from datetime import date
import csv
import os
import re

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import Sum
from django.urls import reverse

from anymail.signals import EventType

from common.utils import nhs_titlecase
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

    def __str__(self):
        return "{} ({})".format(self.name, self.practice_id)

    @property
    def cased_name(self):
        return nhs_titlecase(self.name)

    def total_hits(self):
        return self.intervention_set.aggregate(Sum("hits"))["hits__sum"]

    def save(self, *args, **kwargs):
        fax_number = re.sub(r"[^0-9]", "", self.fax)
        if fax_number and re.search(r"[0-9]{8}", fax_number):
            if fax_number[:2] != "00":
                if fax_number[0] == "0":
                    fax_number = fax_number[1:]
                if fax_number[:2] == "44":
                    fax_number = "00" + fax_number
                else:
                    fax_number = "0044" + fax_number
        self.normalised_fax = fax_number
        super(InterventionContact, self).save(*args, **kwargs)


class Intervention(models.Model):
    METHOD_CHOICES = (("e", "Email"), ("p", "Post"), ("f", "Fax"))
    created_date = models.DateField(default=date.today)
    method = models.CharField(max_length=1, choices=METHOD_CHOICES)
    practice_id = models.CharField(max_length=6)
    metadata = JSONField(null=True, blank=True)
    hits = models.IntegerField(default=0)
    sent = models.BooleanField(default=False)
    generated = models.BooleanField(default=False)
    receipt = models.NullBooleanField(default=None)
    contact = models.ForeignKey(InterventionContact, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("method", "practice_id")
        ordering = ["created_date", "method", "practice_id"]

    def __str__(self):
        # Wondering what get_method_display is? See
        # https://docs.djangoproject.com/en/2.0/ref/models/instances/#django.db.models.Model.get_FOO_display
        if self.method == "e":
            recipient = self.contact.email
        elif self.method == "f":
            recipient = self.contact.fax
        else:
            recipient = self.contact.name
        return "method {}, to {} ({})".format(
            self.get_method_display().lower(),
            self.practice_id,
            "contactable" if self.contactable() else "uncontactable",
        )

    def contactable(self):
        if self.method == "p":
            return True
        return not_empty(self.contact.email)

    def get_absolute_url(self):
        return reverse("views.intervention", args=[self.method, self.practice_id])

    def get_target_url(self):
        # add Google Analytics tracking
        querystring = "utm_source=nimodipine&utm_medium={}".format(
            self.get_method_display().lower()
        )
        target_url = "{}/measure/nimodipine/practice/{}/?{}".format(
            settings.OP_HOST, self.practice_id, querystring
        )
        return target_url

    def mail_logs(self):
        return MailLog.objects.filter(
            tags__contained_by=["nimodipine"], recipient__iexact=self.contact.email
        )

    def set_receipt(self):
        if self.method == "e":
            found = self.mail_logs()
            if found:
                if found.filter(event_type="delivered"):
                    self.receipt = True
                elif found.filter(event_type__in=["bounced", "rejected"]):
                    self.receipt = False
                self.save()

    def get_opened(self):
        if self.method == "e":
            found = self.mail_logs()
            if found:
                if found.filter(event_type="opened"):
                    print("{},{}".format(self.practice_id))

    def message_dir(self):
        location = os.path.join(
            settings.DATA_DIR, self.get_method_display().lower(), self.practice_id
        )
        os.makedirs(location, exist_ok=True)
        return location

    def message_path(self):
        if self.method == "p":
            filename = "letter.pdf"
        elif self.method == "f":
            filename = "fax.pdf"
        elif self.method == "e":
            filename = "email.html"
        return os.path.join(self.message_dir(), filename)

    def is_generated(self):
        if self.generated:
            if os.path.exists(self.message_path()):
                return True
            else:
                raise Exception(
                    "Intervention {} supposedly generated "
                    "but no file at {}".format(self, self.message_path())
                )


# Copied from openprescribing, where this model is created via mailgun
# callbacks
class MailLog(models.Model):
    EVENT_TYPE_CHOICES = [
        (value, value)
        for name, value in vars(EventType).items()
        if not name.startswith("_")
    ]
    metadata = JSONField(null=True, blank=True)
    recipient = models.CharField(max_length=254, db_index=True)
    tags = ArrayField(models.CharField(max_length=100, db_index=True), null=True)
    reject_reason = models.CharField(max_length=15, null=True, blank=True)
    event_type = models.CharField(
        max_length=15, choices=EVENT_TYPE_CHOICES, db_index=True
    )
    timestamp = models.DateTimeField(null=True, blank=True)
    # message = models.ForeignKey(EmailMessage, null=True, db_constraint=False)

    class Meta:
        db_table = "frontend_maillog"
        managed = False

    def __str__(self):
        return "{}: <{}> {}".format(self.timestampe, self.recipient, self.event_type)
