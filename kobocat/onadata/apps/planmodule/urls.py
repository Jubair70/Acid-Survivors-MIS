from django.conf.urls import patterns, include, url
from django.contrib import admin
from onadata.apps.planmodule import views, views_api

urlpatterns = patterns('',
                       url(r'^$', views.index, name='index'),
url(r'^dashboard/$', views.dashboard, name='dashboard'),
                       url(r'^facility_list/$', views.facility_list, name='facility_list'),
                       url(r'^add_facility_form/$', views.add_facility_form, name='add_facility_form'),
                       url(r'^insert_facility_form/$', views.insert_facility_form, name='insert_facility_form'),
                       url(r'^edit_facility_form/(?P<form_id>\d+)/$', views.edit_facility_form,
                           name='edit_facility_form'),
                       url(r'^update_facility_form/$', views.update_facility_form, name='update_facility_form'),
                       url(r'^delete_facility_form/(?P<facility_id>\d+)/$', views.delete_facility_form,
                           name='delete_facility_form'),
                       url(r'^getUpazilas/$', views.getUpazilas, name='getUpazilas'),
                       url(r'^getUnions/$', views.getUnions, name='getUnions'),
                        url(r'^getUnions_asd/$', views.getUnions_asd, name='getUnions_asd'),
                       url(r'^getType/$', views.getType, name='getType'),
                        url(r'^getDashboardData/$', views.getDashboardData, name='getDashboardData'),

                       url(r'^scorecard_list/$', views.scorecard_list, name='scorecard_list'),
                       url(r'^add_scorecard_form/$', views.add_scorecard_form, name='add_scorecard_form'),
                       url(r'^insert_scorecard_form/$', views.insert_scorecard_form, name='insert_scorecard_form'),
                       url(r'^edit_scorecard_form/(?P<scorecard_id>\d+)/$', views.edit_scorecard_form,
                           name='edit_scorecard_form'),
                       url(r'^delete_scorecard_form/(?P<scorecard_id>\d+)/$', views.delete_scorecard_form,
                           name='delete_scorecard_form'),
                       url(r'^update_scorecard_form/$', views.update_scorecard_form, name='update_scorecard_form'),

                       url(r'^scorecard_report/$', views.scorecard_report, name='scorecard_report'),
                       url(r'^getScoreCardData/$', views.getScoreCardData, name='getScoreCardData'),


                        url(r'^csa_report/$', views.csa_report, name='csa_report'),
                        url(r'^getCSAData/$', views.getCSAData, name='getCSAData'),
                        url(r'^test_report/$', views.test_report, name='test_report'),
                        url(r'^getTestData/$', views.getTestData, name='getTestData'),
                        url(r'^economic_empowerment_report/$', views.economic_empowerment_report, name='economic_empowerment_report'),
                        url(r'^getEconomicData/$', views.getEconomicData, name='getEconomicData'),
                       url(r'^dca_list/$', views.dca_list, name='dca_list'),
                       url(r'^add_dca_form/$', views.add_dca_form, name='add_dca_form'),
                       url(r'^insert_dca_form/$', views.insert_dca_form, name='insert_dca_form'),
                       url(r'^delete_dca_form/(?P<dca_id>\d+)/$', views.delete_dca_form, name='delete_dca_form'),
                       url(r'^edit_dca_form/(?P<dca_id>\d+)/$', views.edit_dca_form, name='edit_dca_form'),
                       url(r'^update_dca_form/$', views.update_dca_form, name='update_dca_form'),
                       url(r'^register_household_adolescent/$', views_api.register_household_adolescent),
                       url(r'^get_adolescent_list/$', views_api.get_adolescent_list),
                       url(r'^get_cmp_list/$', views_api.get_cmp_list),
                       url(r'^get_lse_group_list/$', views_api.get_lse_group_list),
                       url(r'^get_comm_orientation_list/$', views_api.get_comm_orientation_list),
                       url(r'^get_csa_list/$', views_api.get_csa_list),
                       url(r'^get_adolescent_list_by_group/$', views_api.get_adolescent_list_by_group),
                       url(r'^get_monthly_cf_form_list/$', views_api.get_monthly_cf_form_list),
                       url(r'^get_session_list_group/$', views_api.get_session_list_group),
                       url(r'^get_makeup_session_data/$', views_api.get_makeup_session_data),
                       url(r'^get_geolocation_csv/$', views_api.get_geolocation_csv),
                       url(r'^upload_monthly_target_plan/$', views_api.upload_monthly_target_plan),
                       url(r'^get_marriage_info_list/$', views_api.get_marriage_info_list),
                       url(r'^get_referrals_list/$', views_api.get_referrals_list),
                       url(r'^commnity_orientation_form/$', views_api.commnity_orientation_form),
                        url(r'^delete_community_orientation/(?P<data_id>\d+)/$', views.delete_community_orientation, name='delete_community_orientation'),

                url(r'^edit_community_orientation/(?P<instance_id>\d+)/$', views.edit_community_orientation, name='edit_community_orientation'),

                       url(r'^mis_report_district_list/$', views.mis_report_district_list,
                           name='mis_report_district_list'),
                       url(r'^add_mis_report_district_form/$', views.add_mis_report_district_form,
                           name='add_mis_report_district_form'),
                       url(r'^insert_mis_report_district_form/$', views.insert_mis_report_district_form,
                           name='insert_mis_report_district_form'),
                       url(r'^edit_mis_report_district_form/(?P<mis_report_id>\d+)/$',
                           views.edit_mis_report_district_form,
                           name='edit_mis_report_district_form'),
                       url(r'^update_mis_report_district_form/$', views.update_mis_report_district_form,
                           name='update_mis_report_district_form'),
                        url(r'^delete_mis_report_district_form/(?P<mis_report_id>\d+)/$', views.delete_mis_report_district_form, name='delete_mis_report_district_form'),
url(r'^community_orientation_list/$', views.community_orientation_list,name='community_orientation_list'),
url(r'^getCommunityData/$', views.getCommunityData, name='getCommunityData'),

                       url(r'^get_upazilas/$', views_api.get_upazilas, name='get_upazilas'),
                       url(r'^get_unions/$', views_api.get_unions, name='get_unions'),
                       url(r'^get_villages/$', views_api.get_villages, name='get_villages'),
                       url(r'^get_paras/$', views_api.get_paras, name='get_paras'),

                       url(r'^submit-xml-data/$', views_api.submitXMLData),
                       url(r'^plan_mis_report/$', views_api.plan_mis_report),
                       url(r'^get_facility_by_upazila/$',views_api.get_facility_by_upazila),


                        url(r'^eyfw/file_share/$', views.file_share, name='file_share'),
                        url(r'^eyfw/getSharedFileList/$', views.getSharedFileList, name='getSharedFileList'),
                        url(r'^eyfw/delete_sharedFile_data/(?P<id>[^/]+)/$', views.delete_sharedFile_data, name='delete_sharedFile_data'),


                        url(r'^analysis_report/$', views.analysis_report, name='analysis_report'),

                       url(r'^get_session_list_by_group_type/$', views_api.get_session_list_by_group_type)

                       )
