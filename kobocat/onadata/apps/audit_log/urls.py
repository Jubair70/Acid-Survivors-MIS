from django.conf.urls import patterns, include, url
from django.contrib import admin
from onadata.apps.audit_log import views

urlpatterns = patterns('',
    # url(r'^$', views.index, name='index'),
    url(r'^mainview/$', views.audit_log_main, name='audit_log_main'),
    url(r"^mainview/(?P<username>\w+)/forms/(?P<id_string>[^/]+)/difference/(?P<instance_id>[^/]+)/did/(?P<data_id>[^/]+)",views.instance_diff, name='difference'),
	url(r'^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/old_json/(?P<instance_id>[\d+^/]+)/did/(?P<data_id>[^/]+)',views.getInstance_json, name='instance_json'),
	url(r"^mainview/(?P<username>\w+)/forms/(?P<id_string>[^/]+)/new_json/(?P<instance_id>[\d+^/]+)/did/(?P<data_id>[^/]+)",views.getInstance_new_json, name='instance_new_json'),
    url(r'^getFormData/$', views.getFormData, name='getFormData'),
    )