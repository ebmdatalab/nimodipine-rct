import base64
import os
import tempfile
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.safestring import SafeText

import requests

from common.utils import grab_image
from antibioticsrct.models import Intervention


def measure_redirect(request, method, wave, practice_id):
    intervention = Intervention.objects.get(
        method=method, wave=wave, practice_id=practice_id)
    intervention.hits += 1
    intervention.save()
    return redirect(intervention.get_target_url())


def intervention_message(request, intervention_id):
    intervention = get_object_or_404(Intervention, pk=intervention_id)
    practice_name = intervention.contact.cased_name
    context = {}
    if intervention.intervention == 'B':
        template = 'intervention_b.html'
    else:
        template = "intervention_a_{}.html".format(intervention.wave)
        if intervention.wave == '3':
            # XXX Cost saving measure. Work out total possible savings
            # this month, savings on that measure, and "switch"
            # wording here.  Poss via API?
            md = intervention.metadata
            context['total_savings'] = round(md['total_savings'])
            context['cost_savings'] = round(md['cost_savings'])
            context['measure_comparison'] = "_{}_comparison.html".format(
                intervention.measure_id)
    with tempfile.NamedTemporaryFile(suffix='.png') as chart_file:
        url = "/practice/{}/".format(intervention.practice_id)
        selector = '#' + intervention.measure_id
        encoded_image = grab_image(url, chart_file.name, selector)
    with open(os.path.join(settings.BASE_DIR, 'antibioticsrct', 'static', 'header.png'), 'rb') as img:
        header_image = base64.b64encode(img.read()).decode('ascii')
    with open(os.path.join(settings.BASE_DIR, 'antibioticsrct', 'static', 'footer.png'), 'rb') as img:
        footer_image = base64.b64encode(img.read()).decode('ascii')
    intervention_url = "http://www.op2.org.uk{}".format(intervention.get_absolute_url())
    intervention_url = '<a href="{}">{}</a>'.format(
        intervention_url, intervention_url)
    context.update({
        'intervention': intervention,
        'practice_name': practice_name,
        'intervention_url': SafeText(intervention_url),
        'encoded_image': encoded_image,
        'header_image': header_image,
        'footer_image': footer_image
    })
    return render(
        request,
        template,
        context=context)
