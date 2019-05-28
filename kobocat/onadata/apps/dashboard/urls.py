from django.conf.urls import patterns, include, url
from django.contrib import admin
from onadata.apps.dashboard import views

urlpatterns = patterns('',

    url(r'^$', views.index, name='index'),
    url(r'^get_member_chart/$', views.get_member_chart, name='get_member_chart'),
    url(r'^generate_saved_report/(?P<id>\d+)/$', views.generate_saved_report, name='generate_saved_report'),
    url(r'^on_change_element/$', views.on_change_element, name='on_change_element'),
    url(r'^on_change_multiple_select/$', views.on_change_multiple_select, name='on_change_multiple_select'),
    url(r'^generate_graph/(?P<graph_id>\d+)/$', views.generate_graph, name='generate_graph'),
    url(r'^save_loaded_dashboard/$', views.save_loaded_dashboard, name='save_loaded_dashboard'),
    url(r'^show_template_get_json/$', views.show_template_get_json, name='show_template_get_json'),
    url(r'^update_loaded_dashboard/(?P<loaded_db_id>\d+)/$', views.update_loaded_dashboard, name='update_loaded_dashboard'),
    url(r'^delete_loaded_dashboard/(?P<loaded_db_id>\d+)/$', views.delete_loaded_dashboard, name='delete_loaded_dashboard'),

    url(r'^get_wmg_tracker_report/$', views.get_wmg_tracker_report, name='get_wmg_tracker_report'),
    url(r'^getWMGTrackerExcel/$', views.getWMGTrackerExcel, name='getWMGTrackerExcel'),

)
