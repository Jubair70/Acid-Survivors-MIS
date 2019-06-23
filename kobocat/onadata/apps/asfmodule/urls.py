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
    url(r'^get_districts/$', views.get_districts,name='get_districts'),
    url(r'^get_upazilas/$', views.get_upazilas,name='get_upazilas'),
    url(r'^get_unions/$', views.get_unions,name='get_unions'),
    url(r'^get_wards/$', views.get_wards,name='get_wards'),
    url(r'^case_list/$', views.case_list,name='case_list'),
    url(r'^add_case_form/$', views.add_case_form,name='add_case_form'),
    url(r'^insert_case_form/$', views.insert_case_form,name='insert_case_form'),
    url(r'^get_case_list/$', views.get_case_list,name='get_case_list'),
    url(r'^case_detail/(?P<case_id>\d+)/$', views.case_detail,name='case_detail'),
    url(r'^update_case_status/(?P<case_id>\d+)/$', views.update_case_status,name='update_case_status'),
    url(r'^get_victim_list/$', views.get_victim_list,name='get_victim_list'),
    url(r'^add_victim/(?P<case_id>\d+)/$', views.add_victim, name='add_victim'),
    url(r'^insert_victim/(?P<case_id>\d+)/$', views.insert_victim, name='insert_victim'),
    url(r'^edit_victim/(?P<victim_tbl_id>\d+)/$', views.edit_victim, name='edit_victim'),
    url(r'^update_victim/(?P<victim_tbl_id>\d+)/$', views.update_victim, name='update_victim'),
    url(r'^victim_status/(?P<victim_tbl_id>\d+)/$', views.victim_status, name='victim_status'),
    url(r'^refer_victim/(?P<victim_tbl_id>\d+)/$', views.refer_victim, name='refer_victim'),
    url(r'^victim_profile/(?P<victim_tbl_id>\d+)/$', views.victim_profile, name='victim_profile'),
    url(r'^victim_list/$', views.victim_list,name='victim_list'),
    url(r'^get_victims_list/$', views.get_victims_list,name='get_victims_list'),

    url(r'^services_to_other_institutes_list/$', views.services_to_other_institutes_list,name='services_to_other_institutes_list'),
    url(r'^get_services_to_other_institutes_list/$', views.get_services_to_other_institutes_list,name='get_services_to_other_institutes_list'),
    url(r'^services_to_other_institutes_form/$', views.services_to_other_institutes_form,name='services_to_other_institutes_form'),

    url(r'^capacity_building_list/$', views.capacity_building_list,name='capacity_building_list'),
    url(r'^get_capacity_building_list/$', views.get_capacity_building_list,name='get_capacity_building_list'),
    url(r'^capacity_building_form/$', views.capacity_building_form,name='capacity_building_form'),

    url(r'^event_list/$', views.event_list,name='event_list'),
    url(r'^get_event_list/$', views.get_event_list,name='get_event_list'),
    url(r'^event_form/$', views.event_form,name='event_form'),

    url(r'^paper_clipping_list/$', views.paper_clipping_list,name='paper_clipping_list'),
    url(r'^get_paper_clipping_list/$', views.get_paper_clipping_list,name='get_paper_clipping_list'),
    url(r'^paper_clipping_form/$', views.paper_clipping_form,name='paper_clipping_form'),
    )
