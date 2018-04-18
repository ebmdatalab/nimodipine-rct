from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

import requests

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
    context = {
        'intervention': intervention,
        'practice_name': practice_name
    }
    if intervention.intervention == 'B':
        template = 'intervention_b.html'
    else:
        template = "intervention_a_{}.html".format(intervention.wave)
        if intervention.wave == '3':
            # XXX Cost saving measure. Work out total possible savings
            # this month, savings on that measure, and "switch"
            # wording here.  Poss via API?
            pass
    return render(
        request,
        template,
        context=context)
