from django.urls import path, re_path
from django.contrib import admin
from antibioticsrct import views

urlpatterns = [
    path('fax_receipt', views.fax_receipt, name='views.fax_receipt'),
    path('msg/<int:intervention_id>', views.intervention_message, name='views.intervention_message'),
    path('msg/random', views.random_intervention_message, name='views.random_intervention_message'),
    re_path(r'(?P<code>[abcdefghkABCDEFGHK]{1})/(?P<practice_id>[A-Z\d]+)/lowpriority', views.measure_redirect, {'lp_focus': True}, name='views.intervention_lowpriority'),
    re_path(r'(?P<code>[abcdefghkABCDEFGHK]{1})/(?P<practice_id>[A-Z\d]+)', views.measure_redirect, name='views.intervention'),
    path('admin/', admin.site.urls),
]
