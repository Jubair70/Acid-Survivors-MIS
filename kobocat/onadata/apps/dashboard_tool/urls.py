from django.conf.urls import patterns, include, url
from django.contrib import admin
from onadata.apps.dashboard_tool import views

urlpatterns = patterns('',

    url(r'^$', views.index, name='index'),

    url(r'^build_dashboard_index/$', views.build_dashboard_index, name='build_dashboard_index'),
    url(r'^generate_chart/$', views.generate_chart, name='generate_chart'),
    url(r'^get_member_chart/$', views.get_member_chart, name='get_member_chart'),
    url(r'^get_generated_graph/$', views.get_generated_graph, name='get_generated_graph'),
    url(r'^generate_graph/(?P<graph_id>\d+)/$', views.generate_graph, name='generate_graph'),
    url(r'^get_graph_json/$', views.get_graph_json, name='get_graph_json'),
    url(r'^show_graph_list/$', views.show_graph_list, name='show_graph_list'),
    url(r'^show_graph_def_get_json/$', views.show_graph_def_get_json, name='show_graph_def_get_json'),
    url(r'^delete_graph_def/(?P<graph_id>\d+)/$', views.delete_graph_def, name='delete_graph_def'),
    url(r'^save_dashboard_style/$', views.save_dashboard_style, name='save_dashboard_style'),

    url(r'^add_navigation_bar/$', views.add_navigation_bar, name='add_navigation_bar'),
    url(r'^show_navigation_bar/$', views.show_navigation_bar, name='show_navigation_bar'),
    url(r'^edit_navigation_bar/(?P<navigation_bar_id>\d+)/$', views.edit_navigation_bar, name='edit_navigation_bar'),
    url(r'^delete_navigation_bar/(?P<navigation_bar_id>\d+)/$', views.delete_navigation_bar, name='delete_navigation_bar'),



    url(r'^add_filtering_control/$', views.add_filtering_control, name='add_filtering_control'),
    url(r'^show_filtering_control/$', views.show_filtering_control, name='show_filtering_control'),
    url(r'^show_filtering_control_get_json/$', views.show_filtering_control_get_json, name='show_filtering_control_get_json'),
    url(r'^delete_filtering_control/(?P<control_id>\d+)/$', views.delete_filtering_control, name='delete_filtering_control'),
    url(r'^edit_filtering_control/(?P<control_id>\d+)/$', views.edit_filtering_control, name='edit_filtering_control'),

)
