from django.conf.urls import patterns, include, url
from django.contrib import admin
from onadata.apps.asfmodule import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^profile_view/(?P<victim_id>\d+)/$', views.profile_view,name='profile_view'),
    url(r'^get_forms_data/$', views.get_forms_data,name='get_forms_data'),
    url(r'^get_data_view/$', views.get_data_view,name='get_data_view'),
    url(r'^get_forms_list/$', views.get_forms_list,name='get_forms_list'),
    url(r'^get_forms_html/$', views.get_forms_html,name='get_forms_html'),
    )
