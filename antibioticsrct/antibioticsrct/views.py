from django.shortcuts import redirect
from .models import Intervention


def measure_redirect(request, method, wave, practice_id):
    intervention = Intervention.objects.get(
        method=method, wave=wave, practice_id=practice_id)
    return redirect(intervention.get_target_url())
