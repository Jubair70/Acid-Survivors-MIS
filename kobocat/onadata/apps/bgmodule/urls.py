from django.conf.urls import patterns, include, url
from django.contrib import admin
from onadata.apps.bgmodule import views

urlpatterns = patterns('',
    url(r'^$', views.wmg_profile_list, name='wmg_profile_list'),
    url(r'^wmg_profile_details/(?P<wmg_id>\d+)/$', views.wmg_profile_details, name='wmg_profile_details'),
    url(r'^wmg_profile_details/$', views.wmg_profile_details, name='wmg_profile_details'),


)
