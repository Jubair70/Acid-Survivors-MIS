from django.conf.urls import patterns, include, url
from django.contrib import admin
from onadata.apps.unicef import views

urlpatterns = patterns('',
    # url(r'^$', views.index, name='index'),
    url(r'^geodata/$', views.geo_index, name='geo_index'),
    url(r'^add-geodata/$', views.add_geodata, name='add_geodata'),
    url(r'^geo-edit/(?P<geo_id>\d+)/$', views.edit_geodata, name='edit_geodata'),
    url(r'^geo-delete/(?P<geo_id>\d+)/$', views.delete_geodata, name='delete_geodata'),
    
    url(r'^geo-rmo-list/$', views.rmo_index, name='rmo_index'),
    url(r'^add-geo-rmo/$', views.add_geo_rmo, name='add_geo_rmo'),
    url(r'^geo-edit-rmo/(?P<rmo_id>\d+)/$', views.edit_geo_rmo, name='edit_geo_rmo'),
    url(r'^geo-delete-rmo/(?P<rmo_id>\d+)/$', views.delete_geo_rmo, name='delete_geo_rmo'),

    url(r'^geo-psu-list/$', views.psu_index, name='psu_index'),
    url(r'^add-geo-psu/$', views.add_geo_psu, name='add_geo_psu'),
    url(r'^geo-edit-psu/(?P<psu_id>\d+)/$', views.edit_geo_psu, name='edit_geo_psu'),
    url(r'^geo-delete-psu/(?P<psu_id>\d+)/$', views.delete_geo_psu, name='delete_geo_psu'),
    # ajax url
    url(r'^get-children/$', views.get_children, name='get_children'),
    url(r'^get-object/$', views.dynamic_ajax, name='dynamic_ajax'),

    url(r'^data/$', views.data_view_project, name='data_view_project'),
    url(r'^unicef_dashboard/$', views.create_dashboard, name='unicef_dashboard'),
    url(r'^unicef_br_report/$', views.create_br_report, name='unicef_br_report'),
    url(r'^get-options/$', views.get_options, name='get_options'),
    
    
    )
