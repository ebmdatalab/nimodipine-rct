import tempfile
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

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
    # XXX also get contact details; potentially from CSV rather than OP API
    if intervention.intervention == 'B':
        template = 'intervention_b.html'
    else:
        template = "intervention_a_{}.html".format(intervention.wave)
        if intervention.wave == '3':
            # XXX Cost saving measure. Work out total possible savings
            # this month, savings on that measure, and "switch"
            # wording here.  Poss via API?
            pass
    with tempfile.NamedTemporaryFile(suffix='.png') as chart_file:
        url = "/practice/{}/".format(intervention.practice_id)
        selector = '#' + intervention.measure_id
        encoded_image = grab_image(url, chart_file.name, selector)
    context = {
        'intervention': intervention,
        'practice_name': practice_name,
        'intervention_url': "http://www.op2.org.uk{}".format(
            intervention.get_absolute_url()),
        'encoded_image': encoded_image,
    }
    return render(
        request,
        template,
        context=context)
