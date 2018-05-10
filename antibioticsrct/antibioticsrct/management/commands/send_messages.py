import glob
import json
import logging
import os
import re

from email.mime.image import MIMEImage
from email.utils import unquote

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail import EmailMultiAlternatives
from django.core.mail import make_msgid
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from anymail.message import attach_inline_image_file
from interfax import InterFAX

from common.utils import email_as_text
from antibioticsrct.models import Intervention
from antibioticsrct.models import InterventionContact


logger = logging.getLogger(__name__)


def inline_images(message, html):
    """Given HTML with inline data images, convert these to attachments,
    and add HTML as an alternative
    """
    images = re.findall(r'<img.*?src="data:image/png;base64,.*?">', html)
    for i, image_tag in enumerate(images):
        filename = "img{}.png".format(i)
        data = re.findall(r'<img.*?src="data:image/png;base64,(.*?)">', image_tag)[0]
        content_id = make_msgid('img')  # Content ID per RFC 2045 section 7 (with <...>)
        image = MIMEImage(data, 'png', _encoder=lambda x: x)
        image.add_header('Content-Disposition', 'inline', filename=filename)
        image.add_header('Content-ID', content_id)
        image.add_header('Content-Transfer-Encoding', 'base64')
        message.attach(image)
        html = html.replace(image_tag, '<img src="cid:{}">'.format(unquote(content_id)))
    message.attach_alternative(html, "text/html")
    return message


def get_intervention_from_path(path):
    # `path` is like
    # /mnt/database/antibiotics-rct-data/interventions/wave1/fax/P84027/fax.pdf
    wave, method, practice_id = re.search(
        r"wave(\d)/(fax|email)/(.*)/.*", path).groups()
    try:
        contact = InterventionContact.objects.get(practice_id=practice_id)
        return contact.intervention_set.get(
            method=method[0], wave=wave)
    except InterventionContact.DoesNotExist:
        logging.error("Could not find contact for practice %s", practice_id)
    except Intervention.DoesNotExist:
        logging.error(
            "Could not find intervention %s/%s for practice %s",
            wave, method, practice_id)


def send_email_message(msg_path, recipient=None, dry_run=False):
    email_path = os.path.join(msg_path, 'email.html')
    with open(email_path, 'r') as body_f:
        body = body_f.read()
        intervention = get_intervention_from_path(email_path)
        if not intervention:
            return
        if intervention.sent:
            logger.info("Refusing to resend %s", intervention)
            return
        logger.info(
            "Sending message to %s", intervention)
        if settings.DEBUG:
            # Belt-and-braces to ensure we don't accidentally send to
            # real users
            to = settings.TEST_EMAIL_TO
        else:
            to = intervention.contact.email
        if recipient:
            # Always allow overriding the test fax recipient
            to = recipient
        subject = 'Information about your prescribing from OpenPrescribing.net'
        msg = EmailMultiAlternatives(
            subject=subject,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to],
            reply_to=[settings.DEFAULT_FROM_EMAIL])
        msg = inline_images(msg, body)
        msg.tags = ["antibioticsrct", "wave{}".format(intervention.wave)]
        msg.body = email_as_text(msg.alternatives[0][0])
        msg.track_clicks = True
        if not dry_run:
            msg.send()
            intervention.sent = True
            intervention.save()


def send_fax_message(msg_path, recipient=None, dry_run=False):
    fax_path = os.path.join(msg_path, 'fax.pdf')
    intervention = get_intervention_from_path(fax_path)
    if not intervention:
        return
    if intervention.sent:
        logger.info("Refusing to resend %s", intervention)
        return
    logger.info(
        "Sending message to %s", intervention)
    if settings.DEBUG:
        to = settings.TEST_FAX_TO
    else:
        to = intervention.contact.normalised_fax
    if recipient:
        # Always allow overriding the test fax recipient
        to = recipient
    # Interfax has 60 character limit on subject
    subject = ("about your prescribing - {}".format(intervention.wave))
    kwargs = {
        'page_header': "To: {To} From: {From} Pages: {TotalPages}",
        'reference': subject,
        'reply_address': settings.FAX_FROM_EMAIL,
        'page_size': 'A4',
        'page_orientation': 'portrait',
        'resolution': 'fine',
        'rendering': 'greyscale',
        'contact': 'Prescribing Lead'}
    interfax = InterFAX(
        username=settings.INTERFAX_USER, password=settings.INTERFAX_PASS)
    if not dry_run:
        interfax.deliver(to, files=[fax_path], **kwargs)
        intervention.sent = True
        intervention.save()


class Command(BaseCommand):
    help = '''Send emails and faxes for given wave'''

    def add_arguments(self, parser):
        parser.add_argument('--wave', type=str)
        parser.add_argument('--test-recipient', type=str)
        parser.add_argument('--method',
                            type=str,
                            default=None,
                            help='If set, generate messages for only this method (e, p, or f)')
        parser.add_argument('--practice',
                            type=str,
                            default=None,
                            help='If set, generate messages for only this practice')
        parser.add_argument('--dry-run',
                            type=bool,
                            default=False,
                            help='If set, do not actually send anything')

    def handle(self, *args, **options):
        wave = "wave{}".format(options['wave'])
        if options['method']:
            methods = [options['method']]
        else:
            methods = ['email', 'fax']
        prompt = "Sending messages in wave {} using method(s) {}".format(wave, methods)
        if options['test_recipient']:
            prompt += " to test recipient {}".format(options['test_recipient'])
        prompt += ". Continue? (y/N)"
        really = input(prompt)
        if really.strip().lower() == 'y':
            for method in methods:
                base_path = os.path.join(settings.DATA_DIR, wave, method)
                if options['practice']:
                    practices = [os.path.join(base_path, options['practice'])]
                else:
                    practices = glob.glob(os.path.join(base_path, '*'))
                for practice_id in practices:
                    msg_path = os.path.join(base_path, practice_id)
                    if method == 'email':
                        send_email_message(msg_path, options['test_recipient'], options['dry_run'])
                    elif method == 'fax':
                        send_fax_message(msg_path, options['test_recipient'], options['dry_run'])
                    else:
                        raise CommandError("method must be 'fax' or 'email'")
