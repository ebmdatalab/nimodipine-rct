from django.urls import path, re_path
from django.contrib import admin
from antibioticsrct import views

urlpatterns = [
    re_path(r'(?P<method>[epfEPF]{1})/(?P<wave>[123]{1})/(?P<practice_id>[A-Z\d]+)', views.measure_redirect, name='views.intervention'),
    path('msg/<int:intervention_id>', views.intervention_message),
    path('admin/', admin.site.urls),
]
