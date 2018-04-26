from django.urls import path, re_path
from django.contrib import admin
from antibioticsrct import views

urlpatterns = [
    path('msg/<int:intervention_id>', views.intervention_message, name='views.intervention_message'),
    path('msg/random', views.random_intervention_message, name='views.random_intervention_message'),
    re_path(r'(?P<code>[abcdefghiABCDEFGHI]{1})/(?P<practice_id>[A-Z\d]+)', views.measure_redirect, name='views.intervention'),
    path('admin/', admin.site.urls),
]
