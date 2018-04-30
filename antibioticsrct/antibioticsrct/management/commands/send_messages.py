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


def send_email_message(msg_path, recipient=None):
    email_path = os.path.join(msg_path, 'email.html')
    metadata_path = os.path.join(msg_path, 'metadata.json')
    with open(email_path, 'r') as body_f, open(metadata_path, 'r') as metadata_f:
        body = body_f.read()
        metadata = json.load(metadata_f)
        logger.info(
            "Sending email message to %s for wave %s", metadata['to'], metadata['wave'])
        metadata['to'] = 'seb.bacon+test@gmail.com'  # XXX testing
        msg = EmailMultiAlternatives(
            subject=metadata['subject'],
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[metadata['to']],
            reply_to=[settings.DEFAULT_FROM_EMAIL])
        if recipient:
            msg.to = [recipient]
        msg = inline_images(msg, body)
        msg.tags = ["antibioticsrct"]
        msg.body = email_as_text(msg.alternatives[0][0])
        msg.track_clicks = True
        msg.send()


def send_fax_message(msg_path, recipient=None):
    fax_path = os.path.join(msg_path, 'fax.pdf')
    metadata_path = os.path.join(msg_path, 'metadata.json')
    with open(metadata_path, 'r') as metadata_f:
        metadata = json.load(metadata_f)
        if recipient:
            to = recipient
        else:
            to = metadata['to']
        to = '00441865289412'  # XXX remove on live
        logger.info(
            "Sending fax to %s for wave %s", to, metadata['wave'])
        # Interfax has 60 character limit on subject
        subject = ("about your prescribing - {}".format(metadata['wave']))
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
        fax = interfax.deliver(to, files=[fax_path], **kwargs)
        fax = fax.reload()
        logger.info("Sent fax id %s, status %s", fax.id, fax.status)


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

    def handle(self, *args, **options):
        wave = "wave{}".format(options['wave'])
        if options['method']:
            methods = [options['method']]
        else:
            methods = ['email', 'fax']
        for method in methods:
            base_path = os.path.join(settings.DATA_DIR, wave, method)
            if options['practice']:
                practices = [os.path.join(base_path, options['practice'])]
            else:
                practices = glob.glob(os.path.join(base_path, '*'))
            for practice_id in practices:
                msg_path = os.path.join(base_path, practice_id)
                if method == 'email':
                    send_email_message(msg_path, options['test_recipient'])
                elif method == 'fax':
                    send_fax_message(msg_path, options['test_recipient'])
                else:
                    raise CommandError("method must be 'fax' or 'email'")
