from django.contrib import admin
from antibioticsrct.models import InterventionContact
from antibioticsrct.models import Intervention
from antibioticsrct.models import MailLog


class InterventionContactAdmin(admin.ModelAdmin):
    list_filter = ('survey_response', 'blacklisted',)
    search_fields = ('practice_id', 'name', 'email',)
admin.site.register(InterventionContact, InterventionContactAdmin)


class InterventionAdmin(admin.ModelAdmin):
    list_filter = ('wave', 'intervention','method','sent', 'receipt')
    search_fields = ('practice_id', 'contact__name', 'contact__email',)
admin.site.register(Intervention, InterventionAdmin)


class MailLogAdmin(admin.ModelAdmin):
    list_filter = ('recipient', 'tags','event_type',)
    search_fields = ('recipient',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(tags__contains=['rct1'])

admin.site.register(MailLog, MailLogAdmin)
