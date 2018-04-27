import base64
import logging
import os
import re
import tempfile

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.template import Context
from django.template import Template
from django.template.loader import render_to_string
from django.utils.safestring import SafeText
from django.views.decorators.csrf import csrf_exempt

import requests

from common.utils import grab_image
from common.utils import decode
from antibioticsrct.models import Intervention
from antibioticsrct.models import get_measure_data

logger = logging.getLogger(__name__)

@csrf_exempt
def fax_receipt(request):
    if request.method == 'POST':
        sender    = request.POST.get('sender')
        recipient = request.POST.get('recipient')
        subject   = request.POST.get('subject', '')
        body_without_quotes = request.POST.get('stripped-text', '')
        recipient = re.findall(r"(\d{7,})", subject)
        wave = re.findall(r"about your prescribing - (\d{1})", subject)
        logger.info("Received email: %s %s %s %s", sender, recipient, subject, body_without_quotes)
        if recipient and wave:
            intervention = get_object_or_404(
                Intervention,
                contact__normalised_fax=recipient[0], method='f', wave=wave[0])
            if 'Successful' in subject:
                intervention.receipt = True
                logger.info("Intervention %s marked as received", intervention)
                intervention.save()
            else:
                logger.warn("Problem sending fax for intervention %s", intervention)
        else:
            logger.warn("Unable to parse intervention")
        return HttpResponse('OK')


def measure_redirect(request, code, practice_id):
    method, wave = decode(code)
    intervention = Intervention.objects.get(
        method=method, wave=wave, practice_id=practice_id)
    if request.POST:
        if request.POST['survey_response'].lower() == 'yes':
            intervention.contact.survey_response = True
        elif request.POST['survey_response'].lower() == 'no':
            intervention.contact.survey_response = False
        intervention.contact.save()
    else:
        intervention.hits += 1
        intervention.save()
        if intervention.hits == 1:
            return render(request, 'questionnaire.html')
    return redirect(intervention.get_target_url())


def random_intervention_message(request):
    """Return a random intervention message. Useful for testing.
    """
    return intervention_message(
        request, Intervention.objects.order_by('?')[0].pk)

def get_measure_comparison(measure, context):
    measure_data = get_measure_data()
    template = Template(measure_data[measure])
    return template.render(Context(context))


def intervention_message(request, intervention_id):
    intervention = get_object_or_404(Intervention, pk=intervention_id)
    practice_name = intervention.contact.cased_name
    context = {}
    if intervention.method == 'p':
        show_header_from = True
        show_header_to = True
    elif intervention.method == 'f':
        show_header_from = True
        show_header_to = False
    else:
        show_header_from = False
        show_header_to = False
    if intervention.intervention == 'B':
        template = 'intervention_b.html'
    else:
        template = "intervention_a_{}.html".format(intervention.wave)
        if intervention.wave == '3':
            md = intervention.metadata
            if md['total_savings']:
                context['total_savings'] = round(md['total_savings'])
            if md['cost_savings']:
                context['cost_savings'] = round(md['cost_savings'])
            context['measure_comparison'] = get_measure_comparison(intervention.measure_id, context)
    with tempfile.NamedTemporaryFile(suffix='.png') as chart_file:
        url = "/practice/{}/".format(intervention.practice_id)
        selector = '#' + intervention.measure_id
        encoded_image = grab_image(url, chart_file.name, selector)
    with open(os.path.join(settings.BASE_DIR, 'antibioticsrct', 'static', 'header.png'), 'rb') as img:
        header_image = base64.b64encode(img.read()).decode('ascii')
    with open(os.path.join(settings.BASE_DIR, 'antibioticsrct', 'static', 'footer.png'), 'rb') as img:
        footer_image = base64.b64encode(img.read()).decode('ascii')
    intervention_url = "op2.org.uk{}".format(intervention.get_absolute_url())
    intervention_url = '<a href="http://{}">{}</a>'.format(
        intervention_url, intervention_url)
    context.update({
        'intervention': intervention,
        'practice_name': practice_name,
        'intervention_url': SafeText(intervention_url),
        'encoded_image': encoded_image,
        'header_image': header_image,
        'footer_image': footer_image,
        'show_header_from': show_header_from,
        'show_header_to': show_header_to
    })
    return render(
        request,
        template,
        context=context)
