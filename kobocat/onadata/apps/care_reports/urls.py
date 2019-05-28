from django.conf.urls import patterns, include, url
from django.contrib import admin
from onadata.apps.care_reports import views

urlpatterns = patterns('',
    # url(r'^$', views.index, name='index'),
    url(r'^bd_attendence_activity/$', views.get_report_bd_attendence_activity, name='get_report_bd_attendence_activity'),
    url(r'^np_attendence_activity/$', views.get_report_np_attendence_activity, name='get_report_np_attendence_activity'),
    url(r'^bd_g_b_status_change/$', views.get_report_bd_girl_boy_status_change, name='get_report_bd_girl_boy_status_change'),
    url(r'^bd_staff_trans/$', views.get_report_bd_staff_transformation, name='get_report_bd_staff_transformation'),
    url(r'^operational-status/$',views.get_report_operation_status,name='get_report_operation_status' ),
    url(r'^bd_obsrv_jrnal/$', views.get_report_bd_obsrv_jrnal, name='get_report_bd_obsrv_jrnal'),
    url(r'^np_g_b_status_change/$', views.get_report_np_girl_boy_status_change, name='get_report_np_girl_boy_status_change'),
    )
