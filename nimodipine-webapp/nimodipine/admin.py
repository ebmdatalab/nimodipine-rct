from django.contrib import admin
from nimodipine.models import InterventionContact
from nimodipine.models import Intervention
from nimodipine.models import MailLog


class InterventionContactAdmin(admin.ModelAdmin):
    list_filter = ("survey_response", "blacklisted")
    search_fields = ("practice_id", "name", "email")


admin.site.register(InterventionContact, InterventionContactAdmin)


class InterventionAdmin(admin.ModelAdmin):
    list_filter = ("method", "sent", "receipt")
    search_fields = ("practice_id", "contact__name", "contact__email")


admin.site.register(Intervention, InterventionAdmin)


class MailLogAdmin(admin.ModelAdmin):
    list_filter = ("recipient", "tags", "event_type")
    search_fields = ("recipient",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(tags__contains=["nimodipine"])


admin.site.register(MailLog, MailLogAdmin)
