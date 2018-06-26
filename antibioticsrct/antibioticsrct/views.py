import base64
import logging
import os
import re
import tempfile

from django.conf import settings
from django.http import HttpResponse
from django.http import Http404
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
        # https://www.interfax.net/en/dev/dev-guide/receive-sent-fax-confirmations-via-callback
        recipient = request.POST.get('DestinationFax')
        subject   = request.POST.get('Subject', '')
        status = request.POST.get('Status', '')
        wave = re.findall(r"about your prescribing - (\d{1})", subject)
        logger.info("Received fax callback: to <%s>, subject <%s>, status <%s>", recipient, subject, status)
        if recipient and wave:
            # It is possible for more than one survey to share a fax machine
            interventions = Intervention.objects.filter(
                contact__normalised_fax=recipient, method='f', wave=wave[0])
            ids = [x.pk for x in interventions]
            if len(ids) == 0:
                raise Http404()
            if status == '0':
                interventions.update(receipt=True)
                logger.info("Intervention %s marked as received", ids)
            elif int(status) > 0:
                interventions.update(receipt=False)
                logger.warn(
                    "Problem sending fax for intervention %s (status %s)",
                    ids,
                    status)
            else:
                logger.info(
                    "Received temporary fax status for intervention %s (status %s)",
                    ids,
                    status)
        else:
            logger.warn("Unable to parse intervention")
        return HttpResponse('OK')


def measure_redirect(request, code, practice_id, lp_focus=False):
    method, wave = decode(code)
    intervention = Intervention.objects.get(
        method=method, wave=wave, practice_id=practice_id)
    if request.POST:
        # The user has filled out the one-off interstitial
        # questionnaire
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
    if lp_focus:
        # A special URL that drills down to the individual "low
        # priority" measures
        return redirect(intervention.get_target_url(lp_focus=True))
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
    show_header_from = True
    if intervention.method == 'p':
        show_header_to = True
    else:
        show_header_to = False
    if intervention.intervention == 'B':
        template = 'intervention_b.html'
    else:
        template = "intervention_a_{}.html".format(intervention.wave)
        if intervention.wave == '3':
            lp_focus_url = "op2.org.uk{}".format(
                intervention.get_absolute_url(lp_focus=True))
            lp_focus_url = '<a href="http://{}">{}</a>'.format(
                lp_focus_url, lp_focus_url)
            context['lp_focus_url'] = SafeText(lp_focus_url)
            md = intervention.metadata  # generated in the generate_wave command
            if md['total_savings']:
                context['total_savings'] = round(md['total_savings'])
            if md['lp_spend']:
                # We assume all spend on LP stuff can be stopped. This
                # is an overestimate: Only 14 of them are "don't use"
                # recommendations and the others would require some
                # kind of switch.
                context['cost_savings'] = round(md['lp_spend'])
            if md['cost_savings']:
                context['cost_savings'] = round(md['cost_savings'])
            context['measure_comparison'] = get_measure_comparison(intervention.measure_id, context)
    with tempfile.NamedTemporaryFile(suffix='.png') as chart_file:
        url = "/practice/{}/".format(intervention.practice_id)
        if intervention.measure_id == 'low-priority':
            selector = '#' + 'lpzomnibus'
        else:
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
