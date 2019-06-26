#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Count, Q
from django.http import (
    HttpResponseRedirect, HttpResponse)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, loader
from django.contrib.auth.models import User
from datetime import date, timedelta, datetime
# from django.utils import simplejson
import json
import logging
import sys
import operator
import pandas
from django.shortcuts import render
import numpy
import time
import datetime
from django.core.files.storage import FileSystemStorage

from django.core.urlresolvers import reverse

from django.db import (IntegrityError, transaction)
from django.db.models import ProtectedError
from django.shortcuts import redirect
from onadata.apps.main.models.user_profile import UserProfile
from onadata.apps.usermodule.forms import UserForm, UserProfileForm, ChangePasswordForm, UserEditForm, OrganizationForm, \
    OrganizationDataAccessForm, ResetPasswordForm
from onadata.apps.usermodule.models import UserModuleProfile, UserPasswordHistory, UserFailedLogin, Organizations, \
    OrganizationDataAccess

from django.contrib.auth.decorators import login_required, user_passes_test
from django import forms
# Menu imports
from onadata.apps.usermodule.forms import MenuForm
from onadata.apps.usermodule.models import MenuItem
# Unicef Imports
from onadata.apps.logger.models import Instance, XForm
# Organization Roles Import
from onadata.apps.usermodule.models import OrganizationRole, MenuRoleMap, UserRoleMap
from onadata.apps.usermodule.forms import OrganizationRoleForm, RoleMenuMapForm, UserRoleMapForm, UserRoleMapfForm
from django.forms.models import inlineformset_factory, modelformset_factory
from django.forms.formsets import formset_factory

from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from collections import OrderedDict
import decimal
import os


def __db_fetch_values(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchall()
    cursor.close()
    return fetchVal


def __db_fetch_single_value(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchone()
    cursor.close()
    return fetchVal[0]


def __db_fetch_values_dict(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = dictfetchall(cursor)
    cursor.close()
    return fetchVal


def __db_commit_query(query):
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    cursor.close()


def dictfetchall(cursor):
    desc = cursor.description
    return [
        OrderedDict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()]


def decimal_date_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        return obj
    raise TypeError


@login_required
def index(request):
    return render(request, 'planmodule/index.html')

@login_required
def dashboard(request):
    # Rectangle Count
    query = "with enrol as(with t as ( select date_submitted::date,array_length(string_to_array(adolescent_name,' '),1)::int enroll from vw_lse_grp_members) select sum(enroll)::int enrolled from t), all_ses_cnt as (with m as(with q as( with t as ( select count(*) as c, group_id, group_type from vw_grp_reg_sessions group by group_id, group_type) select * from t where group_type::int in ( 1, 3) and c = 5 union all select * from t where group_type::int in ( 2, 4 ) and c = 8 ), p as (select unnest(string_to_array( adolescent_name, ' ' )) as adolescent_id, group_id from vw_grp_reg_sessions ), z as (with s as ( with k as ( select distinct on ( session, id_adolescent ) * from vw_grp_all_sessions) select count(*) as c, id_adolescent, group_type from k group by id_adolescent, group_type ) select id_adolescent from s where ( s.c > 4 and group_type::int in ( 1, 3 )) or ( s.c > 7 and group_type::int in ( 2, 4 ))) select distinct p.adolescent_id from q, p where p.group_id in ( select group_id from q ) and p.adolescent_id in ( select id_adolescent from z )) select count( adolescent_id )::int as no_of_adol_com_all_ses from m), referrel as (select count(*)::int refer from vw_plan_referral_reg) ,ref_fol as (select count(*)::int ref_fol from vw_referral_followup)select  coalesce(enrolled,0) enrolled,no_of_adol_com_all_ses all_ses_cnt,refer referrel,ref_fol from enrol,all_ses_cnt,referrel,ref_fol"
    df = pandas.DataFrame()
    df = pandas.read_sql(query,connection)
    enrolled = df.enrolled.tolist()[0]
    all_ses_cnt = df.all_ses_cnt.tolist()[0]
    referrel = df.referrel.tolist()[0]
    ref_fol = df.ref_fol.tolist()[0]


    # Map
    query_for_map_data = "with t as(select json->>'upazila' upazila,json_array_elements((json->>'ado_info')::json) ado_info from logger_instance where xform_id = 549 and deleted_at is null)select (select field_name from geo_data where geocode = upazila) upazila_name,count(*)::int ado_total from t group by upazila_name"
    df = pandas.DataFrame()
    df = pandas.read_sql(query_for_map_data,connection)

    stat = 0
    min_range = []
    max_range = []
    if not df.empty:
        stat = 1
        min_val = min(df.ado_total.tolist())
        max_val = max(df.ado_total.tolist())
        if min_val == max_val:
            min_val = 0
        range = (max_val - min_val)/8

        temp_min = min_val
        temp_max = min_val + range

        i = 0
        while i<8:
            min_range.append(temp_min)
            max_range.append(temp_max)
            temp_min = temp_max + 1
            temp_max = temp_min + range
            i = i + 1


    result_json = []
    file = open("onadata/media/all_geojson/rangpur.geojson", 'r')
    json_content = file.read()
    file.close()
    json_content = json.loads(json_content)['features']
    # print(min_range)
    # print(max_range)

    for each in json_content:
        if not df[df['upazila_name']==each['properties']['Upazila']]['ado_total'].empty:
            each['properties']['ado_total'] = df[df['upazila_name']==each['properties']['Upazila']]['ado_total'].tolist()[0]
            each['properties']['color'] = color_range(min_range,max_range,each['properties']['ado_total'])
        else:
            each['properties']['ado_total'] = 0
            each['properties']['color'] = color_range(min_range, max_range, each['properties']['ado_total'])


    query_for_table = "select 'LSE completed' as event,count(*) total_session from vw_grp_reg_sessions union all select 'Issue Specific meeting participants' as event,count(*) total_session from vw_comm_orientation where orientation_type::int = 4 union all select 'TFD shows' as event,count(*) total_session from plan_mis_report_district_form where activity_id in('IR2_4C_32','IR3_2A_38') union all select 'Orientation for married adolescents' as event,count(*) total_session from vw_comm_orientation where orientation_type::int = 3 union all select 'Orientation for change agents' as event,count(*) total_session from plan_mis_report_district_form where activity_id in ('IR2_3C_28','IR2_3C_29') union all select 'Positive deviant couples' as event,count(*) total_session from vw_comm_orientation where married_adolescent_or_couple_type::int = 2 union all select 'Exposure visit participants' as event,count(*) total_session from vw_cf_miscellaneous_activity where activity_name = 'IR2_4A_30' union all (with t as ( select json->>'id_adolescent' counts from logger_instance where xform_id = 540 and deleted_at is null) select 'No of child marriage prevented' as event, count(counts) total_session from t) union all select 'Community score cards ' as event,count(*) total_session from plan_scorecard union all select 'School based programs by guest speakers' as event,count(*) total_session from vw_cf_miscellaneous_activity where activity_name = 'IR3_3F_51' union all select 'School based programs by teachers' as event,count(*) total_session from vw_cf_miscellaneous_activity where activity_name = 'IR3_3F_53'"
    df = pandas.DataFrame()
    df = pandas.read_sql(query_for_table,connection)
    total_session = df.total_session.tolist()

    query_for_adol_count_chart = "with t as( select group_type,sum(array_length(string_to_array(adolescent_name, ' '),1)::int) total from vw_lse_grp_members group by group_type),t1 as(select sum(total) all_total from t), t3 as ( select '1' group_type union select '2' group_type union select '3' group_type union select '4' group_type ), tt as( select group_type,round(total*100/all_total,0) percentage from t,t1 ) select t3.group_type,coalesce(percentage,0) percentage from t3 left outer join tt on t3.group_type = tt.group_type order by group_type"
    df = pandas.DataFrame()
    df = pandas.read_sql(query_for_adol_count_chart, connection)
    adolescent_percentage = df.percentage.tolist()

    query_for_adol_service = "with t as( select referral_place,count(*) total from vw_referral_followup where got_service::int = 1 group by referral_place),t1 as (select sum(total) all_total from t), t3 as ( select 'Maternal and Child Welfare Center (MCWC)' as referral_place union all select 'Upazila Health Complex (UHC)' as referral_place union all select 'Union Health and Family Welfare Center (UHFWC)' as referral_place union all select 'Rural Dispensary (RD)' as referral_place union all select 'Family Welfare Center (FWC)' as referral_place union all select 'Community Clinic (CC)' as referral_place union all select 'Surjer Hashi Clinics' as referral_place union all select 'SMC Blue Star Center' as referral_place union all select 'Others' as referral_place ), tt as ( select referral_place,round(total*100/all_total,0) percentage from t,t1 )select t3.referral_place,coalesce(percentage,0) percentage from t3 left join tt on t3.referral_place = tt.referral_place order by referral_place"
    df = pandas.DataFrame()
    df = pandas.read_sql(query_for_adol_service, connection)
    adolescent_serv_percentage = df.percentage.tolist()
    return render(request, 'planmodule/dashboard.html',{'adolescent_serv_percentage':adolescent_serv_percentage,'adolescent_percentage':adolescent_percentage,'total_session':total_session,'result_json': json.dumps(json_content),'enrolled':enrolled
                                                        ,'all_ses_cnt':all_ses_cnt,
                                                        'referrel':referrel,
                                                        'ref_fol':ref_fol,'min_range':min_range,'max_range':max_range,'stat':stat})


def color_range(min_range,max_range,cnt):
    colors = ['#b2b2ff','#9999ff','#7f7fff','#6666ff','#4c4cff','#3232ff','#1919ff','#0000ff']
    i = 0
    while i<8 and len(min_range) and len(max_range):
        if cnt >= min_range[i] and cnt <= max_range[i]:
            return colors[i]
        i = i + 1
    return colors[0]


@login_required
def getDashboardData(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = "with enrol as(with t as ( select date_submitted::date,array_length(string_to_array(adolescent_name,' '),1)::int enroll from vw_lse_grp_members where date_submitted between '"+str(from_date)+"' and '"+str(to_date)+"') select sum(enroll)::int enrolled from t), all_ses_cnt as (with m as(with q as( with t as ( select count(*) as c, group_id, group_type from vw_grp_reg_sessions group by group_id, group_type) select * from t where group_type::int in ( 1, 3) and c = 5 union all select * from t where group_type::int in ( 2, 4 ) and c = 8 ), p as (select unnest(string_to_array( adolescent_name, ' ' )) as adolescent_id, group_id from vw_grp_reg_sessions ), z as (with s as ( with k as ( select distinct on ( session, id_adolescent ) * from vw_grp_all_sessions where session_date::date between '"+str(from_date)+"' and '"+str(to_date)+"') select count(*) as c, id_adolescent, group_type from k group by id_adolescent, group_type ) select id_adolescent from s where ( s.c > 4 and group_type::int in ( 1, 3 )) or ( s.c > 7 and group_type::int in ( 2, 4 ))) select distinct p.adolescent_id from q, p where p.group_id in ( select group_id from q ) and p.adolescent_id in ( select id_adolescent from z )) select count( adolescent_id )::int as no_of_adol_com_all_ses from m), referrel as (select count(*)::int refer from vw_plan_referral_reg where refferal_date::date between '"+str(from_date)+"' and '"+str(to_date)+"') ,ref_fol as (select count(*)::int ref_fol from vw_referral_followup where refferal_date::date between '"+str(from_date)+"' and '"+str(to_date)+"')select coalesce(enrolled,0) enrolled,no_of_adol_com_all_ses all_ses_cnt,refer referrel,ref_fol from enrol,all_ses_cnt,referrel,ref_fol"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    enrolled = df.enrolled.tolist()[0]
    all_ses_cnt = df.all_ses_cnt.tolist()[0]
    referrel = df.referrel.tolist()[0]
    ref_fol = df.ref_fol.tolist()[0]

    # Map
    query_for_map_data = "with t as (select json->>'upazila' upazila,json_array_elements((json->>'ado_info')::json)  ado_info from logger_instance where xform_id = 549 and deleted_at is null and (json->>'start')::date between '"+str(from_date)+"' and '"+str(to_date)+"')select (select field_name from geo_data where geocode = upazila) upazila_name,count(*)::int ado_total from t group by upazila_name"
    df = pandas.DataFrame()
    df = pandas.read_sql(query_for_map_data, connection)

    stat = 0
    min_range = []
    max_range = []
    if not df.empty:
        stat = 1
        min_val = min(df.ado_total.tolist())
        max_val = max(df.ado_total.tolist())
        if min_val == max_val:
            min_val = 0
        range = (max_val - min_val) / 8

        temp_min = min_val
        temp_max = min_val + range

        i = 0
        while i < 8:
            min_range.append(temp_min)
            max_range.append(temp_max)
            temp_min = temp_max + 1
            temp_max = temp_min + range
            i = i + 1

    result_json = []
    file = open("onadata/media/all_geojson/rangpur.geojson", 'r')
    json_content = file.read()
    file.close()
    json_content = json.loads(json_content)['features']

    for each in json_content:
        if not df[df['upazila_name'] == each['properties']['Upazila']]['ado_total'].empty:
            each['properties']['ado_total'] = \
            df[df['upazila_name'] == each['properties']['Upazila']]['ado_total'].tolist()[0]
            each['properties']['color'] = color_range(min_range, max_range, each['properties']['ado_total'])
        else:
            each['properties']['ado_total'] = 0
            each['properties']['color'] = color_range(min_range, max_range, each['properties']['ado_total'])

    query_for_table = "SELECT 'LSE completed' AS event, Count(*) total_session FROM vw_grp_reg_sessions where session_date between '"+str(from_date)+"' and '"+str(to_date)+"' UNION ALL SELECT 'Issue Specific meeting participants' AS event, Count(*) total_session FROM vw_comm_orientation where orientation_type :: INT = 4 and \"date\" between '"+str(from_date)+"' and '"+str(to_date)+"' UNION ALL SELECT 'TFD shows' AS event, Count(*) total_session FROM plan_mis_report_district_form WHERE activity_id IN( 'IR2_4C_32', 'IR3_2A_38') and activity_date::date between '"+str(from_date)+"' and '"+str(to_date)+"' UNION ALL SELECT 'Orientation for married adolescents' AS event, Count(*) total_session FROM vw_comm_orientation WHERE orientation_type :: INT = 3 and \"date\" between '"+str(from_date)+"' and '"+str(to_date)+"' UNION ALL SELECT 'Orientation for change agents' AS event, Count(*) total_session FROM plan_mis_report_district_form WHERE activity_id IN( 'IR2_3C_28', 'IR2_3C_29' ) and activity_date::date between '"+str(from_date)+"' and '"+str(to_date)+"' UNION ALL SELECT 'Positive deviant couples' AS event, Count(*) total_session FROM vw_comm_orientation WHERE married_adolescent_or_couple_type :: INT = 2 and \"date\" between '"+str(from_date)+"' and '"+str(to_date)+"' UNION ALL SELECT 'Exposure visit participants' AS event, Count(*) total_session FROM vw_cf_miscellaneous_activity WHERE activity_name = 'IR2_4A_30' and activity_date::date between '"+str(from_date)+"' and '"+str(to_date)+"' UNION ALL ( WITH t AS (SELECT json ->> 'id_adolescent' counts FROM logger_instance WHERE xform_id = 540 AND deleted_at IS null and (json->>'date_child_marriage_prevented')::date between '"+str(from_date)+"' and '"+str(to_date)+"') SELECT 'No of child marriage prevented' AS event, Count(counts) total_session FROM t) UNION ALL SELECT 'Community score cards ' AS event, Count(*) total_session FROM plan_scorecard where execution_date::date between '"+str(from_date)+"' and '"+str(to_date)+"' UNION ALL SELECT 'School based programs by guest speakers' AS event, Count(*) total_session FROM vw_cf_miscellaneous_activity WHERE activity_name = 'IR3_3F_51' and activity_date::date between '"+str(from_date)+"' and '"+str(to_date)+"' UNION ALL SELECT 'School based programs by teachers' AS event, Count(*) total_session FROM vw_cf_miscellaneous_activity WHERE activity_name = 'IR3_3F_53' and activity_date::date between '"+str(from_date)+"' and '"+str(to_date)+"'"
    df = pandas.DataFrame()
    df = pandas.read_sql(query_for_table, connection)
    total_session = df.total_session.tolist()

    query_for_adol_count_chart = "WITH t AS( SELECT group_type, Sum(Array_length(String_to_array(adolescent_name, ' '),1)::int) total FROM vw_lse_grp_members where date_submitted::date between '"+str(from_date)+"' and '"+str(to_date)+"' GROUP BY group_type),t1 AS ( SELECT Sum(total) all_total FROM t), t3 AS ( SELECT '1' group_type UNION SELECT '2' group_type UNION SELECT '3' group_type UNION SELECT '4' group_type), tt AS ( SELECT group_type, Round(total*100/all_total,0) percentage FROM t, t1 ) SELECT t3.group_type, COALESCE(percentage,0) percentage FROM t3 LEFT OUTER JOIN tt ON t3.group_type = tt.group_type ORDER BY group_type;"
    df = pandas.DataFrame()
    df = pandas.read_sql(query_for_adol_count_chart, connection)
    adolescent_percentage = df.percentage.tolist()

    query_for_adol_service = "WITH t AS( SELECT referral_place, Count(*) total FROM vw_referral_followup WHERE got_service::int = 1 and follow_up_date::date between '"+str(from_date)+"' and '"+str(to_date)+"' GROUP BY referral_place),t1 AS ( SELECT Sum(total) all_total FROM t), t3 AS ( SELECT 'Maternal and Child Welfare Center (MCWC)' AS referral_place UNION ALL SELECT 'Upazila Health Complex (UHC)' AS referral_place UNION ALL SELECT 'Union Health and Family Welfare Center (UHFWC)' AS referral_place UNION ALL SELECT 'Rural Dispensary (RD)' AS referral_place UNION ALL SELECT 'Family Welfare Center (FWC)' AS referral_place UNION ALL SELECT 'Community Clinic (CC)' AS referral_place UNION ALL SELECT 'Surjer Hashi Clinics' AS referral_place UNION ALL SELECT 'SMC Blue Star Center' AS referral_place UNION ALL SELECT 'Others' AS referral_place), tt AS ( SELECT referral_place, Round(total*100/all_total,0) percentage FROM t, t1 ) SELECT t3.referral_place, COALESCE(percentage,0) percentage FROM t3 LEFT JOIN tt ON t3.referral_place = tt.referral_place ORDER BY referral_place"
    df = pandas.DataFrame()
    df = pandas.read_sql(query_for_adol_service, connection)
    adolescent_serv_percentage = df.percentage.tolist()
    data = json.dumps({'enrolled': enrolled,
                       'all_ses_cnt': all_ses_cnt,
                       'referrel': referrel,
                       'ref_fol': ref_fol,
                       'result_json': json.dumps(json_content),
                       'min_range':min_range,
                       'max_range':max_range,
                       'total_session':total_session,
                       'adolescent_percentage': adolescent_percentage,
                       'adolescent_serv_percentage':adolescent_serv_percentage
                       })
    return HttpResponse(data)



def get_recursive_organization_children(organization, organization_list=[]):
    organization_list.append(organization)
    observables = Organizations.objects.filter(parent_organization=organization)
    for org in observables:
        if org not in organization_list:
            organization_list = list((set(get_recursive_organization_children(org, organization_list))))
    return list(set(organization_list))


@login_required
def facility_list(request):
    current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
    if current_user:
        current_user = current_user[0]

    # fetching all organization recursively of current_user
    all_organizations = get_recursive_organization_children(current_user.organisation_name, [])
    org_id_list = [org.pk for org in all_organizations]
    org = str(map(str, org_id_list))
    org = org.replace('[', '(').replace(']', ')')
    query = "select id,DATE(registration_date) registration_date, (select field_name from geo_data where id = district) district,(select field_name from geo_data where id = upazilla) upazilla, facilty_name, facilty_id,Case when facility_type = 1 then 'FWCC' when facility_type = 2 then 'CC' when facility_type = 3 then 'MCWC'  when facility_type = 4 then 'UHC'  when facility_type = 5 then 'USC'  when facility_type = 6 then 'UH'   end facility_type from plan_facilities where pngo_id in " + str(
        org)
    facility_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)

    return render(request, 'planmodule/facility_list.html', {
        'facility_list': facility_list
    })


@login_required
def add_facility_form(request):
    query = "select id,field_name from geo_data where field_type_id = 86"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    dist_id = df.id.tolist()
    dist_name = df.field_name.tolist()
    district = zip(dist_id, dist_name)
    user_id = request.user.id
    query = "select id,organization from public.usermodule_organizations where id = ( select organisation_name_id from public.usermodule_usermoduleprofile where user_id = " + str(
        user_id) + ")"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()[0]
    org_name = df.organization.tolist()[0]

    prev_facility_id_query = "select distinct facilty_id from plan_facilities"
    df = pandas.DataFrame()
    df = pandas.read_sql(prev_facility_id_query, connection)
    facility_list = df.facilty_id.tolist()
    # print(facility_list)
    return render(request, 'planmodule/add_facility_form.html',
                  {'district': district, 'org_id': org_id, 'org_name': org_name,'facility_list':json.dumps(facility_list)})


@login_required
def insert_facility_form(request):
    if request.POST:
        registration_date = request.POST.get('registration_date')
        district = request.POST.get('district')
        upazilla = request.POST.get('upazila')
        # union = request.POST.get('union')
        facilty_name = request.POST.get('facility_name')
        facilty_id = request.POST.get('facility_id')
        facility_type = request.POST.get('facility_type')
        pngo_id = request.POST.get('org_id')
        user_id = request.user.id
        insert_query = "INSERT INTO public.plan_facilities (registration_date, district, upazilla,  facilty_name, facilty_id,facility_type,created_by,pngo_id) VALUES('" + str(
            registration_date) + "', " + str(district) + ", " + str(upazilla) + ", '" + str(
            facilty_name) + "', '" + str(facilty_id) + "','" + str(facility_type) + "'," + str(user_id) + "," + str(
            pngo_id) + ")"
        __db_commit_query(insert_query)
        messages.success(request, '<i class="fa fa-check-circle"></i> New Facility has been added successfully!',
                             extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/planmodule/facility_list/")


@login_required
def edit_facility_form(request, form_id):
    query = "select DATE(registration_date) registration_date,(select field_name from geo_data where id = district) district_name,(select field_name from geo_data where id = upazilla) upazilla_name,  district, upazilla,  facilty_name, facilty_id,facility_type from plan_facilities where id=" + str(
        form_id) + ""
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    data = {}
    data['form_id'] = form_id
    data['registration_date'] = df.registration_date.tolist()[0]
    data['facilty_name'] = df.facilty_name.tolist()[0]
    data['facilty_id'] = df.facilty_id.tolist()[0]
    facility_type = df.facility_type.tolist()[0]
    district_id = df.district.tolist()[0]
    district_name = df.district_name.tolist()[0]
    upazila_id = df.upazilla.tolist()[0]
    upazilla_name = df.upazilla_name.tolist()[0]
    # xunion_id = df.xunion.tolist()[0]
    # xunion_name = df.union_name.tolist()[0]


    query = "select id,field_name from geo_data where field_type_id = 88 and field_parent_id = " + str(district_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    upz_id = df.id.tolist()
    upz_name = df.field_name.tolist()
    upazila = zip(upz_id, upz_name)

    # query = "select id,field_name from geo_data where field_type_id = 89 "
    # df = pandas.DataFrame()
    # df = pandas.read_sql(query, connection)
    # union_id = df.id.tolist()
    # union_name = df.field_name.tolist()
    # union = zip(union_id, union_name)

    query = "select id,organization from public.usermodule_organizations where id = (select pngo_id from public.plan_facilities where id = " + str(
        form_id) + ")"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()[0]
    org_name = df.organization.tolist()[0]
    return render(request, 'planmodule/edit_facility_form.html',
                  {'data': json.dumps(data, default=decimal_date_default), 'district_id': district_id,
                   'district_name': district_name, 'upazila_id': upazila_id, 'upazilla_name': upazilla_name,
                   'upazila': upazila, 'org_id': org_id, 'org_name': org_name,'facility_type':facility_type})


@login_required
def update_facility_form(request):
    if request.POST:
        form_id = request.POST.get('form_id')
        registration_date = request.POST.get('registration_date')
        district = request.POST.get('district')
        upazilla = request.POST.get('upazila')
        # union = request.POST.get('union')
        facilty_name = request.POST.get('facility_name')
        facilty_id = request.POST.get('facility_id')
        facility_type = request.POST.get('facility_type')
        pngo_id = request.POST.get('org_id')
        user_id = request.user.id
        update_query = "UPDATE public.plan_facilities SET registration_date='" + str(
            registration_date) + "', district=" + str(district) + ", upazilla=" + str(
            upazilla) + ",  facilty_name='" + str(facilty_name) + "', facilty_id='" + str(
            facilty_id) + "', created_at=now(),facility_type=" + str(facility_type) + ", created_by=" + str(
            user_id) + ",pngo_id = " + str(pngo_id) + " WHERE id=" + str(form_id)
        __db_commit_query(update_query)
        messages.success(request, '<i class="fa fa-check-circle"></i> Facility has been updated successfully!',
                             extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/planmodule/facility_list/")


@login_required
def delete_facility_form(request, facility_id):
    delete_query = "delete from plan_facilities where id = " + str(facility_id) + ""
    __db_commit_query(delete_query)
    messages.success(request, '<i class="fa fa-check-circle"></i> Facility has been deleted successfully!',
                             extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/planmodule/facility_list/")


def getUpazilas(request):
    district = request.POST.get('dist')
    query = "select geoid from usermodule_catchment_area where user_id = " +str(request.user.id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    if not df.empty and  df.geoid.tolist()[0] != 9377:
        geoid = df.geoid.tolist()[0]
        upazila_query = "select id,field_name from geo_data where field_type_id = 88 and field_parent_id = " + str(district) +" and id ="+str(geoid)
        upazila_data = json.dumps(__db_fetch_values_dict(upazila_query))
    else:
        upazila_query = "select id,field_name from geo_data where field_type_id = 88 and field_parent_id = " + str(district)
        upazila_data = json.dumps(__db_fetch_values_dict(upazila_query))
    return HttpResponse(upazila_data)


def getUnions(request):
    upazila = request.POST.get('upz')
    union_query = "select id,field_name from geo_data where field_type_id = 89 and field_parent_id = (select id from geo_data where geocode = '"+str(upazila)+"')"
    union_data = json.dumps(__db_fetch_values_dict(union_query))
    return HttpResponse(union_data)

def getUnions_asd(request):
    upazila = json.loads(request.POST.get('upz'))
    upazila = str(map(int, upazila))
    upazila = upazila.replace('[','').replace(']','').replace(' ', '')  
    union_query = "select geocode as id,field_name from geo_data where field_type_id = 89 and field_parent_id = any(select id from geo_data where geocode = any(string_to_array('"+str(upazila)+"',',')))"
    union_data = json.dumps(__db_fetch_values_dict(union_query))
    return HttpResponse(union_data)


@login_required
def scorecard_list(request):
    current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
    if current_user:
        current_user = current_user[0]

    # fetching all organization recursively of current_user
    all_organizations = get_recursive_organization_children(current_user.organisation_name, [])
    org_id_list = [org.pk for org in all_organizations]
    org = str(map(str, org_id_list))
    org = org.replace('[', '(').replace(']', ')')
    query = "select id,(select field_name from public.geo_data where id = district) district,(select field_name from public.geo_data where id = upazilla) upazilla,DATE(execution_date) execution_date,(select facilty_name from public.plan_facilities where facilty_id::int = facility_id limit 1 ) facility_name,case when facility_type = 1 then 'FWCC' else 'CC' end facility_type,average_score_adolescents,average_score_service_providers,major_comments_adolescents,major_comments_service_providers from public.plan_scorecard where pngo_id in " + str(
        org)
    scorecard_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)

    return render(request, 'planmodule/scorecard_list.html', {
        'scorecard_list': scorecard_list
    })


@login_required
def add_scorecard_form(request):
    query = "select id,field_name from geo_data where field_type_id = 86"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    dist_id = df.id.tolist()
    dist_name = df.field_name.tolist()
    district = zip(dist_id, dist_name)
    user_id = request.user.id
    query = "select id,organization from public.usermodule_organizations where id = ( select organisation_name_id from public.usermodule_usermoduleprofile where user_id = " + str(
        user_id) + ")"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()[0]
    org_name = df.organization.tolist()[0]

    query = "select facilty_id,facilty_name from plan_facilities"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    facility_id = df.facilty_id.tolist()
    facility_name = df.facilty_name.tolist()
    facility = zip(facility_id, facility_name)
    return render(request, 'planmodule/add_scorecard_form.html',
                  {'district': district, 'org_id': org_id, 'org_name': org_name, 'facility': facility})


def getType(request):
    facility_id = request.POST.get('obj')
    facility_query = "select facility_type from plan_facilities where facilty_id::int = " + str(facility_id)
    facility_type = json.dumps(__db_fetch_values_dict(facility_query))
    return HttpResponse(facility_type)


@login_required
def insert_scorecard_form(request):
    if request.POST:
        execution_date = request.POST.get('execution_date')
        district = request.POST.get('district')
        upazilla = request.POST.get('upazila')
        # union = request.POST.get('union')
        facility_id = request.POST.get('facility_name')
        facility_type = request.POST.get('facility_type')
        pngo_id = request.POST.get('org_id')
        created_by = request.user.id
        updated_by = request.user.id
        # from_date = request.POST.get('from_date')
        # to_date = request.POST.get('to_date')
        average_score_adolescents = request.POST.get('average_score_adolescents')
        average_score_service_providers = request.POST.get('average_score_service_providers')
        major_comments_adolescents = request.POST.get('major_comments_adolescents')
        major_comments_service_providers = request.POST.get('major_comments_service_providers')
        insert_query = "INSERT INTO public.plan_scorecard ( district, upazilla, pngo_id, execution_date, facility_id, facility_type, average_score_adolescents, average_score_service_providers, major_comments_adolescents, major_comments_service_providers, created_by, updated_by, created_at, updated_at) VALUES(" + str(
            district) + ", " + str(upazilla) + ", " + str(pngo_id) + ", '" + str(execution_date) + "', " + str(facility_id) + ", " + str(facility_type) + ", " + str(
            average_score_adolescents) + ", " + str(average_score_service_providers) + ", '" + str(
            major_comments_adolescents) + "', '" + str(major_comments_service_providers) + "', " + str(
            created_by) + ", " + str(updated_by) + ",now(),now())"
        __db_commit_query(insert_query)
        messages.success(request, '<i class="fa fa-check-circle"></i> New Score card has been added successfully!',
                             extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/planmodule/scorecard_list/")


@login_required
def edit_scorecard_form(request, scorecard_id):
    query = "select id,district,(select field_name from public.geo_data where id = district) district_name,upazilla,(select field_name from public.geo_data where id = upazilla) upazilla_name,DATE(execution_date) execution_date,facility_id,(select facilty_name from public.plan_facilities where facilty_id::int = facility_id) facility_name, facility_type,average_score_adolescents,average_score_service_providers,major_comments_adolescents,major_comments_service_providers from public.plan_scorecard where id=" + str(
        scorecard_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    data = {}
    data['scorecard_id'] = scorecard_id
    execution_date = df.execution_date.tolist()[0]
    data['facility_type'] = df.facility_type.tolist()[0]
    data['average_score_adolescents'] = df.average_score_adolescents.tolist()[0]
    data['average_score_service_providers'] = df.average_score_service_providers.tolist()[0]
    data['major_comments_adolescents'] = df.major_comments_adolescents.tolist()[0]
    data['major_comments_service_providers'] = df.major_comments_service_providers.tolist()[0]
    district_id = df.district.tolist()[0]
    district_name = df.district_name.tolist()[0]
    upazila_id = df.upazilla.tolist()[0]
    upazilla_name = df.upazilla_name.tolist()[0]
    set_facility_id = df.facility_id.tolist()[0]
    set_facility_name = df.facility_name.tolist()[0]
    # print(data['execution_date'])

    query = "select id,field_name from geo_data where field_type_id = 88 and field_parent_id = " + str(district_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    upz_id = df.id.tolist()
    upz_name = df.field_name.tolist()
    upazila = zip(upz_id, upz_name)

    query = "select id,organization from public.usermodule_organizations where id = (select pngo_id from public.plan_scorecard where id = " + str(
        scorecard_id) + ")"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()[0]
    org_name = df.organization.tolist()[0]

    query = "select facilty_id,facilty_name from plan_facilities"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    facility_id = df.facilty_id.tolist()
    facility_name = df.facilty_name.tolist()
    facility = zip(facility_id, facility_name)
    return render(request, 'planmodule/edit_scorecard_form.html',
                  {'data': json.dumps(data, default=decimal_date_default), 'district_id': district_id,
                   'district_name': district_name, 'upazila_id': upazila_id, 'upazilla_name': upazilla_name,
                   'upazila': upazila, 'org_id': org_id, 'org_name': org_name, 'set_facility_id': set_facility_id,
                   'set_facility_name': set_facility_name, 'facility': facility, 'execution_date': execution_date
                      })



@login_required
def update_scorecard_form(request):
    if request.POST:
        scorecard_id = request.POST.get('scorecard_id')
        execution_date = request.POST.get('execution_date')
        district = request.POST.get('district')
        upazilla = request.POST.get('upazila')
        facility_id = request.POST.get('facility_name')
        facility_type = request.POST.get('facility_type')
        pngo_id = request.POST.get('org_id')
        updated_by = request.user.id
        # from_date = request.POST.get('from_date')
        # to_date = request.POST.get('to_date')
        average_score_adolescents = request.POST.get('average_score_adolescents')
        average_score_service_providers = request.POST.get('average_score_service_providers')
        major_comments_adolescents = request.POST.get('major_comments_adolescents')
        major_comments_service_providers = request.POST.get('major_comments_service_providers')
        update_query = "UPDATE public.plan_scorecard SET district=" + str(district) + ", upazilla=" + str(
            upazilla) + ", pngo_id=" + str(pngo_id) + ", execution_date='" + str(
            execution_date) + "', facility_id=" + str(facility_id) + ", facility_type=" + str(
            facility_type) + ", average_score_adolescents=" + str(
            average_score_adolescents) + ", average_score_service_providers=" + str(
            average_score_service_providers) + ", major_comments_adolescents='" + str(
            major_comments_adolescents) + "', major_comments_service_providers='" + str(
            major_comments_service_providers) + "',  updated_by=" + str(
            updated_by) + ", updated_at=now() WHERE id=" + str(scorecard_id)
        __db_commit_query(update_query)
        messages.success(request, '<i class="fa fa-check-circle"></i> Score card has been updated successfully!',
                             extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/planmodule/scorecard_list/")



@login_required
def delete_scorecard_form(request, scorecard_id):
    delete_query = "delete from plan_scorecard where id = " + str(scorecard_id) + ""
    __db_commit_query(delete_query)
    messages.success(request, '<i class="fa fa-check-circle"></i> Score card has been deleted successfully!',
                             extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/planmodule/scorecard_list/")



@login_required
def scorecard_report(request):
    current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
    if current_user:
        current_user = current_user[0]

    # fetching all organization recursively of current_user
    all_organizations = get_recursive_organization_children(current_user.organisation_name, [])
    org_id_list = [org.pk for org in all_organizations]
    org = str(map(str, org_id_list))
    org = org.replace('[', '(').replace(']', ')')

    query_pngo = "select id,organization from public.usermodule_organizations where id in "+str(org)
    df = pandas.DataFrame()
    df = pandas.read_sql(query_pngo,connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id,org_name)

    query = "select geoid from usermodule_catchment_area where user_id = (select id from auth_user where username = '"+str(current_user)+"')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    if df.empty:
        query = "select id,(select field_name from public.geo_data where id = district limit 1) district,(select field_name from public.geo_data where id = upazilla limit 1) upazilla,DATE(execution_date) execution_date,(select facilty_name from public.plan_facilities where facilty_id::int = facility_id limit 1) facility_name,case when facility_type = 1 then 'FWCC' else 'CC' end facility_type,average_score_adolescents,average_score_service_providers,major_comments_adolescents,major_comments_service_providers from public.plan_scorecard where pngo_id in " + str(
            org)
        scorecard_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
        query = "select id,field_name from geo_data where field_type_id = 88 "
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        upz_id = df.id.tolist()
        upz_name = df.field_name.tolist()
        upazila = zip(upz_id, upz_name)
    else:
        geoid = df.geoid.tolist()[0]

        query = "select * from geo_data where id ="+str(geoid)
        df = pandas.DataFrame()
        df = pandas.read_sql(query,connection)
        if not df.empty and df.field_type_id.tolist()[0] == 86:
            district_geoid = df.id.tolist()[0]
            query = "select id,(select field_name from public.geo_data where id = district limit 1) district,(select field_name from public.geo_data where id = upazilla limit 1) upazilla,DATE(execution_date) execution_date,(select facilty_name from public.plan_facilities where facilty_id::int = facility_id limit 1) facility_name,case when facility_type = 1 then 'FWCC' else 'CC' end facility_type,average_score_adolescents,average_score_service_providers,major_comments_adolescents,major_comments_service_providers from public.plan_scorecard where district = "+str(district_geoid)+" and  pngo_id in " + str(
            org)
            scorecard_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
            # print(query)
            query = "select id,field_name from geo_data where field_type_id = 88 "
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            upz_id = df.id.tolist()
            upz_name = df.field_name.tolist()
            upazila = zip(upz_id, upz_name)
        elif not df.empty and df.field_type_id.tolist()[0] == 88:
            upazila_geoid = df.id.tolist()[0]
            query = "select id,(select field_name from public.geo_data where id = district limit 1) district,(select field_name from public.geo_data where id = upazilla limit 1) upazilla,DATE(execution_date) execution_date,(select facilty_name from public.plan_facilities where facilty_id::int = facility_id limit 1) facility_name,case when facility_type = 1 then 'FWCC' else 'CC' end facility_type,average_score_adolescents,average_score_service_providers,major_comments_adolescents,major_comments_service_providers from public.plan_scorecard where upazilla = "+str(upazila_geoid)+" and  pngo_id in " + str(
            org)
            scorecard_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
            query = "select id,field_name from geo_data where field_type_id = 88 and id = "+str(upazila_geoid)
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            upz_id = df.id.tolist()
            upz_name = df.field_name.tolist()
            upazila = zip(upz_id, upz_name)

        
        

    return render(request, 'planmodule/scorecard_report.html', {
        'scorecard_list': scorecard_list,'organization':organization,'upazila':upazila
    })


@login_required
def getScoreCardData(request):
    current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
    if current_user:
        current_user = current_user[0]
    all_organizations = get_recursive_organization_children(current_user.organisation_name, [])
    org_id_list = [org.pk for org in all_organizations]
    org = str(map(str, org_id_list))
    org = org.replace('[', '(').replace(']', ')')

    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    upazila = request.POST.get('upazila')
    pngo = request.POST.get('pngo')
    filter_query = "where  execution_date between '" + str(from_date) + "' and '" + str(to_date) + "'"
    if upazila !="":
        filter_query += " and upazilla = "+str(upazila)
    else:
        query = "select geoid,(select field_type_id from geo_data where id = geoid) from usermodule_catchment_area where user_id = "+str(request.user.id)
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        if not df.empty and df.field_type_id.tolist()[0]==88:
            upazila_geoid = df.geoid.tolist()[0]
            filter_query += " and upazilla = " + str(upazila_geoid)
        elif not df.empty and df.field_type_id.tolist()[0]==86:
            district_geoid = df.geoid.tolist()[0]
            filter_query += " and district = " + str(district_geoid)
    if pngo !="":
        filter_query += " and pngo_id = "+str(pngo)
    else:
        filter_query += " and pngo_id in " + str(org)
    query = "select id,(select field_name from public.geo_data where id = district limit 1) district,(select field_name from public.geo_data where id = upazilla limit 1) upazilla,DATE(execution_date) execution_date,(select facilty_name from public.plan_facilities where facilty_id::int = facility_id limit 1) facility_name,case when facility_type = 1 then 'FWCC' else 'CC' end facility_type,average_score_adolescents,average_score_service_providers,major_comments_adolescents,major_comments_service_providers from public.plan_scorecard "+str(filter_query)
    # print(query)
    scorecard_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(scorecard_list)


@login_required
def csa_report(request):
    current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
    if current_user:
        current_user = current_user[0]

    # fetching all organization recursively of current_user
    all_organizations = get_recursive_organization_children(current_user.organisation_name, [])
    org_id_list = [org.pk for org in all_organizations]
    org = str(map(int, org_id_list))
    org = org.replace('[', '(').replace(']', ')')

    query = "select geoid,(select field_type_id from geo_data where id = geoid),(select geocode from geo_data where id = geoid) from usermodule_catchment_area where user_id = (select id from auth_user where username = '"+str(current_user)+"')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    

    if df.empty:
        query_t = "WITH csa_reg AS(SELECT json ->> 'info/id_adolescent' id_adolescent, json ->> 'info/adolescent_name' adolescent_name , json->>'info/district' district_id, json ->> 'info/upazila' upazilla_id, json ->> 'info/union_name' union_id, json ->> 'business_start_month' business_start_month , (SELECT id FROM PUBLIC.usermodule_organizations WHERE organization = ( json ->> 'info/pngo')) pngo_id, json ->> 'info/pngo' pngo_name FROM PUBLIC.logger_instance WHERE xform_id = 555 AND deleted_at IS NULL), csa_reg_follow AS (SELECT json ->> 'info/id_adolescent' id_adolescent, json ->> 'month' current_month, json ->> 'received_commodity_price' commodity_price, json ->> 'sold_commodity_price' commodity_amount, json ->> 'profit' profit, json ->> 'remarks' remarks FROM PUBLIC.logger_instance WHERE xform_id = 554 AND deleted_at IS NULL) SELECT csa_reg.*, current_month,coalesce(commodity_price,'')commodity_price,coalesce(commodity_amount,'') commodity_amount,coalesce(remarks,'') remarks,coalesce(profit,'') profit FROM csa_reg, csa_reg_follow WHERE csa_reg.id_adolescent = csa_reg_follow.id_adolescent"
        query = "select geocode,field_name from geo_data where field_type_id = 88"
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        upz_id = df.geocode.tolist()
        upz_name = df.field_name.tolist()
        upazila = zip(upz_id, upz_name)
        query = "select geocode,field_name from geo_data where field_type_id = 89 "
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        union_id = df.geocode.tolist()
        union_name = df.field_name.tolist()
        union = zip(union_id, union_name)       
    elif not df.empty:
        geoid = df.geoid.tolist()[0]
        geocode = df.geocode.tolist()[0]
        if df.field_type_id.tolist()[0] == 86:
            query_t = "WITH csa_reg AS(SELECT json ->> 'info/id_adolescent' id_adolescent, json ->> 'info/adolescent_name' adolescent_name , json->>'info/district' district_id, json ->> 'info/upazila' upazilla_id, json ->> 'info/union_name' union_id, json ->> 'business_start_month' business_start_month , (SELECT id FROM PUBLIC.usermodule_organizations WHERE organization = ( json ->> 'info/pngo')) pngo_id, json ->> 'info/pngo' pngo_name FROM PUBLIC.logger_instance WHERE xform_id = 555 AND deleted_at IS NULL), csa_reg_follow AS (SELECT json ->> 'info/id_adolescent' id_adolescent, json ->> 'month' current_month, json ->> 'received_commodity_price' commodity_price, json ->> 'sold_commodity_price' commodity_amount, json ->> 'profit' profit, json ->> 'remarks' remarks FROM PUBLIC.logger_instance WHERE xform_id = 554 AND deleted_at IS NULL) SELECT csa_reg.*, current_month,coalesce(commodity_price,'')commodity_price,coalesce(commodity_amount,'') commodity_amount,coalesce(remarks,'') remarks,coalesce(profit,'') profit FROM csa_reg, csa_reg_follow WHERE csa_reg.id_adolescent = csa_reg_follow.id_adolescent and pngo_id in "+str(org)

            query = "select geocode,field_name from geo_data where field_type_id = 88"
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            upz_id = df.geocode.tolist()
            upz_name = df.field_name.tolist()
            upazila = zip(upz_id, upz_name)
            query = "select geocode,field_name from geo_data where field_type_id = 89 "
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            union_id = df.geocode.tolist()
            union_name = df.field_name.tolist()
            union = zip(union_id, union_name)
        elif df.field_type_id.tolist()[0] == 88:

            query_t = "WITH csa_reg AS(SELECT json ->> 'info/id_adolescent' id_adolescent, json ->> 'info/adolescent_name' adolescent_name , json->>'info/district' district_id, json ->> 'info/upazila' upazilla_id, json ->> 'info/union_name' union_id, json ->> 'business_start_month' business_start_month , (SELECT id FROM PUBLIC.usermodule_organizations WHERE organization = ( json ->> 'info/pngo')) pngo_id, json ->> 'info/pngo' pngo_name FROM PUBLIC.logger_instance WHERE xform_id = 555 AND deleted_at IS NULL), csa_reg_follow AS (SELECT json ->> 'info/id_adolescent' id_adolescent, json ->> 'month' current_month, json ->> 'received_commodity_price' commodity_price, json ->> 'sold_commodity_price' commodity_amount, json ->> 'profit' profit, json ->> 'remarks' remarks FROM PUBLIC.logger_instance WHERE xform_id = 554 AND deleted_at IS NULL) SELECT csa_reg.*, current_month,coalesce(commodity_price,'')commodity_price,coalesce(commodity_amount,'') commodity_amount,coalesce(remarks,'') remarks,coalesce(profit,'') profit FROM csa_reg, csa_reg_follow WHERE csa_reg.id_adolescent = csa_reg_follow.id_adolescent and pngo_id in "+str(org)+" and upazilla_id::bigint = "+str(geocode)
            query = "select geocode,field_name from geo_data where field_type_id = 88 and id = "+str(geoid)
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            upz_id = df.geocode.tolist()
            upz_name = df.field_name.tolist()
            upazila = zip(upz_id, upz_name)
            query = "select geocode,field_name from geo_data where field_type_id = 89 and field_parent_id = "+str(geoid)
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            union_id = df.geocode.tolist()
            union_name = df.field_name.tolist()
            union = zip(union_id, union_name)

        elif df.field_type_id.tolist()[0] == 89:
            query_t = "WITH csa_reg AS(SELECT json ->> 'info/id_adolescent' id_adolescent, json ->> 'info/adolescent_name' adolescent_name , json->>'info/district' district_id, json ->> 'info/upazila' upazilla_id, json ->> 'info/union_name' union_id, json ->> 'business_start_month' business_start_month , (SELECT id FROM PUBLIC.usermodule_organizations WHERE organization = ( json ->> 'info/pngo')) pngo_id, json ->> 'info/pngo' pngo_name FROM PUBLIC.logger_instance WHERE xform_id = 555 AND deleted_at IS NULL), csa_reg_follow AS (SELECT json ->> 'info/id_adolescent' id_adolescent, json ->> 'month' current_month, json ->> 'received_commodity_price' commodity_price, json ->> 'sold_commodity_price' commodity_amount, json ->> 'profit' profit, json ->> 'remarks' remarks FROM PUBLIC.logger_instance WHERE xform_id = 554 AND deleted_at IS NULL) SELECT csa_reg.*, current_month ,coalesce(commodity_price,'')commodity_price,coalesce(commodity_amount,'') commodity_amount,coalesce(remarks,'') remarks,coalesce(profit,'') profit FROM csa_reg, csa_reg_follow WHERE csa_reg.id_adolescent = csa_reg_follow.id_adolescent and pngo_id in "+str(org)+" and union_id::bigint = "+str(geocode)

            query = "select geocode,field_name from geo_data where field_type_id = 88 and id = (select field_parent_id from geo_data where id = "+str(geoid)+")"
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            upz_id = df.geocode.tolist()
            upz_name = df.field_name.tolist()
            upazila = zip(upz_id, upz_name)
            query = "select geocode,field_name from geo_data where field_type_id = 89 and id = "+str(geoid)
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            union_id = df.geocode.tolist()
            union_name = df.field_name.tolist()
            union = zip(union_id, union_name)

    csa_list = json.dumps(__db_fetch_values_dict(query_t), default=decimal_date_default)

    query_pngo = "select id,organization from public.usermodule_organizations where id in "+str(org)
    df = pandas.DataFrame()
    df = pandas.read_sql(query_pngo,connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id,org_name)

    

    return render(request, 'planmodule/csa_report.html', {
        'csa_list': csa_list,'organization':organization,'upazila':upazila,'union':union
    })


@login_required
def getCSAData(request):
    current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
    if current_user:
        current_user = current_user[0]
    all_organizations = get_recursive_organization_children(current_user.organisation_name, [])
    org_id_list = [org.pk for org in all_organizations]
    org = str(map(str, org_id_list))
    org = org.replace('[', '(').replace(']', ')')


    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    upazila = request.POST.get('upazila')
    union = request.POST.get('union')
    pngo = request.POST.get('pngo')

    filter_query = "and  business_start_month between '" + str(from_date) + "' and '" + str(to_date) + "'"

    if upazila !="":
        filter_query += " and upazilla_id::int  = "+str(upazila)
    else:
        query = "select geoid,(select field_type_id from geo_data where id = geoid),(select geocode from geo_data where id = geoid) from usermodule_catchment_area where user_id = "+str(request.user.id)
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        if not df.empty and df.field_type_id.tolist()[0]==88:
            upazila_geocode = df.geocode.tolist()[0]
            filter_query += " and upazilla_id = '" + str(upazila_geocode)+"'"
        elif not df.empty and df.field_type_id.tolist()[0]==86:
            district_geocode = df.geocode.tolist()[0]
            filter_query += " and district_id = '" + str(district_geocode)+"'"

    if pngo !="":
        filter_query += " and pngo_id = '"+str(pngo)+"'"
    else:
        filter_query += " and pngo_id in " + str(org)


    if union!="":
        filter_query += " and union_id = '" + str(union)+"'"

    query = "WITH csa_reg AS(SELECT json ->> 'info/id_adolescent' id_adolescent, json ->> 'info/adolescent_name' adolescent_name , json->>'info/district' district_id, json ->> 'info/upazila' upazilla_id, json ->> 'info/union_name' union_id, json ->> 'business_start_month' business_start_month , (SELECT id FROM PUBLIC.usermodule_organizations WHERE organization = ( json ->> 'info/pngo')) pngo_id, json ->> 'info/pngo' pngo_name FROM PUBLIC.logger_instance WHERE xform_id = 555 AND deleted_at IS NULL), csa_reg_follow AS (SELECT json ->> 'info/id_adolescent' id_adolescent, json ->> 'month' current_month, json ->> 'received_commodity_price' commodity_price, json ->> 'sold_commodity_price' commodity_amount, json ->> 'profit' profit, json ->> 'remarks' remarks FROM PUBLIC.logger_instance WHERE xform_id = 554 AND deleted_at IS NULL) SELECT csa_reg.*, current_month,coalesce(commodity_price,'')commodity_price,coalesce(commodity_amount,'') commodity_amount,coalesce(remarks,'') remarks,coalesce(profit,'') profit FROM csa_reg, csa_reg_follow WHERE csa_reg.id_adolescent = csa_reg_follow.id_adolescent "+str(filter_query)
    
    csa_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(csa_list)


@login_required
def test_report(request):
    current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
    if current_user:
        current_user = current_user[0]

    # fetching all organization recursively of current_user
    all_organizations = get_recursive_organization_children(current_user.organisation_name, [])
    org_id_list = [org.pk for org in all_organizations]
    org = str(map(str, org_id_list))
    org = org.replace('[', '(').replace(']', ')')

    query = "select geoid,(select field_type_id from geo_data where id = geoid),(select geocode from geo_data where id = geoid) from usermodule_catchment_area where user_id = (select id from auth_user where username = '"+str(current_user)+"')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)

    if df.empty:
        query_t = "with t as( SELECT username, village_geocode, village_name, union_geocode, union_name, upazilla_geocode, upazilla_name, district_geocode, district_name, group_type, maritial_status, submission_date, test_type, group_id, adolescent_name, id_adolescent, number_obtained,case when number_obtained::int <=5 then 1 else 0 end poor,case when number_obtained::int >=6 and number_obtained::int <=9 then 1 else 0 end good,case when number_obtained::int >=10 then 1 else 0 end excellent FROM public.vw_life_skill_education_test)select group_id,case when test_type='1' then 'Pre' else 'Post' end test_type,submission_date,count(adolescent_name) enrolled,sum(poor) poor,sum(good) good,sum(excellent) excellent from t group by submission_date,test_type,group_id"
        query_for_chart = "with t as( SELECT username, village_geocode, village_name, union_geocode, union_name, upazilla_geocode, upazilla_name, district_geocode, district_name, group_type, maritial_status, submission_date, test_type, group_id, adolescent_name, id_adolescent, number_obtained,case when number_obtained::int <=5 then 1 else 0 end poor,case when number_obtained::int >=6 and number_obtained::int <=9 then 1 else 0 end good,case when number_obtained::int >=10 then 1 else 0 end excellent FROM public.vw_life_skill_education_test)select test_type,sum(poor) poor,sum(good) good,sum(excellent) excellent from t group by test_type order by test_type"
        query = "select geocode,field_name from geo_data where field_type_id = 88"
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        upz_id = df.geocode.tolist()
        upz_name = df.field_name.tolist()
        upazila = zip(upz_id, upz_name)

        query = "select geocode,field_name from geo_data where field_type_id = 89 "
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        union_id = df.geocode.tolist()
        union_name = df.field_name.tolist()
        union = zip(union_id, union_name)

        query = "select id,username from auth_user where id in (select user_id from usermodule_catchment_area where geoid in (select id from geo_data where field_type_id = 89))"
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        user_id = df.id.tolist()
        user_name = df.username.tolist()
        user = zip(user_id, user_name)

    elif not df.empty:
        geoid = df.geoid.tolist()[0]
        geocode = df.geocode.tolist()[0]

        if df.field_type_id.tolist()[0] == 86:
            query_t = "with t as( SELECT username, village_geocode, village_name, union_geocode, union_name, upazilla_geocode, upazilla_name, district_geocode, district_name, group_type, maritial_status, submission_date, test_type, group_id, adolescent_name, id_adolescent, number_obtained,case when number_obtained::int <=5 then 1 else 0 end poor,case when number_obtained::int >=6 and number_obtained::int <=9 then 1 else 0 end good,case when number_obtained::int >=10 then 1 else 0 end excellent FROM public.vw_life_skill_education_test where pngo_id in "+str(org)+")select group_id,case when test_type='1' then 'Pre' else 'Post' end test_type,submission_date,count(adolescent_name) enrolled,sum(poor) poor,sum(good) good,sum(excellent) excellent from t group by submission_date,test_type,group_id"
            query_for_chart = "with t as( SELECT username, village_geocode, village_name, union_geocode, union_name, upazilla_geocode, upazilla_name, district_geocode, district_name, group_type, maritial_status, submission_date, test_type, group_id, adolescent_name, id_adolescent, number_obtained,case when number_obtained::int <=5 then 1 else 0 end poor,case when number_obtained::int >=6 and number_obtained::int <=9 then 1 else 0 end good,case when number_obtained::int >=10 then 1 else 0 end excellent FROM public.vw_life_skill_education_test where pngo_id in "+str(org)+")select test_type,sum(poor) poor,sum(good) good,sum(excellent) excellent from t group by test_type order by test_type"
            query = "select geocode,field_name from geo_data where field_type_id = 88"
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            upz_id = df.geocode.tolist()
            upz_name = df.field_name.tolist()
            upazila = zip(upz_id, upz_name)

            query = "select geocode,field_name from geo_data where field_type_id = 89 "
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            union_id = df.geocode.tolist()
            union_name = df.field_name.tolist()
            union = zip(union_id, union_name)

            query = "with recursive t as( select id,field_name,field_type_id from geo_data where id = (select geoid from usermodule_catchment_area where user_id = "+str(request.user.id)+") union all select geo_data.id,geo_data.field_name,geo_data.field_type_id from geo_data,t where geo_data.field_parent_id = t.id)select id,username from auth_user where id in (select user_id from usermodule_catchment_area k where k.geoid in (select id from t where field_type_id = 89))"
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            user_id = df.id.tolist()
            user_name = df.username.tolist()
            user = zip(user_id, user_name)

        elif df.field_type_id.tolist()[0] == 88:

            query_t = "with t as( SELECT username, village_geocode, village_name, union_geocode, union_name, upazilla_geocode, upazilla_name, district_geocode, district_name, group_type, maritial_status, submission_date, test_type, group_id, adolescent_name, id_adolescent, number_obtained,case when number_obtained::int <=5 then 1 else 0 end poor,case when number_obtained::int >=6 and number_obtained::int <=9 then 1 else 0 end good,case when number_obtained::int >=10 then 1 else 0 end excellent FROM public.vw_life_skill_education_test where pngo_id in "+str(org)+" and upazilla_geocode = '"+str(geocode)+"' )select group_id,case when test_type='1' then 'Pre' else 'Post' end test_type,submission_date,count(adolescent_name) enrolled,sum(poor) poor,sum(good) good,sum(excellent) excellent from t group by submission_date,test_type,group_id "
            query_for_chart = "with t as( SELECT username, village_geocode, village_name, union_geocode, union_name, upazilla_geocode, upazilla_name, district_geocode, district_name, group_type, maritial_status, submission_date, test_type, group_id, adolescent_name, id_adolescent, number_obtained,case when number_obtained::int <=5 then 1 else 0 end poor,case when number_obtained::int >=6 and number_obtained::int <=9 then 1 else 0 end good,case when number_obtained::int >=10 then 1 else 0 end excellent FROM public.vw_life_skill_education_test where pngo_id in "+str(org)+" and upazilla_geocode = '"+str(geocode)+"')select test_type,sum(poor) poor,sum(good) good,sum(excellent) excellent from t group by test_type order by test_type"
            query = "select geocode,field_name from geo_data where field_type_id = 88 and id = "+str(geoid)
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            upz_id = df.geocode.tolist()
            upz_name = df.field_name.tolist()
            upazila = zip(upz_id, upz_name)

            query = "select geocode,field_name from geo_data where field_type_id = 89 and field_parent_id = "+str(geoid)
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            union_id = df.geocode.tolist()
            union_name = df.field_name.tolist()
            union = zip(union_id, union_name)

            query = "with recursive t as( select id,field_name,field_type_id from geo_data where id = (select geoid from usermodule_catchment_area where user_id = "+str(request.user.id)+") union all select geo_data.id,geo_data.field_name,geo_data.field_type_id from geo_data,t where geo_data.field_parent_id = t.id)select id,username from auth_user where id in (select user_id from usermodule_catchment_area k where k.geoid in (select id from t where field_type_id = 89))"
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            user_id = df.id.tolist()
            user_name = df.username.tolist()
            user = zip(user_id, user_name)            

        elif df.field_type_id.tolist()[0] == 89:
            query_t = "with t as( SELECT username, village_geocode, village_name, union_geocode, union_name, upazilla_geocode, upazilla_name, district_geocode, district_name, group_type, maritial_status, submission_date, test_type, group_id, adolescent_name, id_adolescent, number_obtained,case when number_obtained::int <=5 then 1 else 0 end poor,case when number_obtained::int >=6 and number_obtained::int <=9 then 1 else 0 end good,case when number_obtained::int >=10 then 1 else 0 end excellent FROM public.vw_life_skill_education_test where pngo_id in "+str(org)+" and union_geocode = '"+str(geocode)+"' )select group_id,case when test_type='1' then 'Pre' else 'Post' end test_type,submission_date,count(adolescent_name) enrolled,sum(poor) poor,sum(good) good,sum(excellent) excellent from t group by submission_date,test_type,group_id"
            query_for_chart = "with t as( SELECT username, village_geocode, village_name, union_geocode, union_name, upazilla_geocode, upazilla_name, district_geocode, district_name, group_type, maritial_status, submission_date, test_type, group_id, adolescent_name, id_adolescent, number_obtained,case when number_obtained::int <=5 then 1 else 0 end poor,case when number_obtained::int >=6 and number_obtained::int <=9 then 1 else 0 end good,case when number_obtained::int >=10 then 1 else 0 end excellent FROM public.vw_life_skill_education_test where pngo_id in "+str(org)+" and union_geocode = '"+str(geocode)+"')select test_type,sum(poor) poor,sum(good) good,sum(excellent) excellent from t group by test_type order by test_type"
            query = "select geocode,field_name from geo_data where field_type_id = 88 and id = (select field_parent_id from geo_data where id = "+str(geoid)+")"
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            upz_id = df.geocode.tolist()
            upz_name = df.field_name.tolist()
            upazila = zip(upz_id, upz_name)

            query = "select geocode,field_name from geo_data where field_type_id = 89 and id = "+str(geoid)
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            union_id = df.geocode.tolist()
            union_name = df.field_name.tolist()
            union = zip(union_id, union_name)

            query = "with recursive t as( select id,field_name,field_type_id from geo_data where id = (select geoid from usermodule_catchment_area where user_id = "+str(request.user.id)+") union all select geo_data.id,geo_data.field_name,geo_data.field_type_id from geo_data,t where geo_data.field_parent_id = t.id)select id::int,username from auth_user where id in (select user_id from usermodule_catchment_area k where k.geoid in (select id from t where field_type_id = 89))"
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            user_id = df.id.tolist()
            user_name = df.username.tolist()
            user = zip(user_id, user_name)



    # print(query_t)
    # query = "with t as( SELECT username, village_geocode, village_name, union_geocode, union_name, upazilla_geocode, upazilla_name, district_geocode, district_name, group_type, maritial_status, submission_date, test_type, group_id, adolescent_name, id_adolescent, number_obtained,case when number_obtained::int <=5 then 1 else 0 end poor,case when number_obtained::int >=6 and number_obtained::int <=9 then 1 else 0 end good,case when number_obtained::int >=10 then 1 else 0 end excellent FROM public.vw_life_skill_education_test where pngo_id in "+str(org)+")select group_id,case when test_type='1' then 'Pre' else 'Post' end test_type,submission_date,count(adolescent_name) enrolled,sum(poor) poor,sum(good) good,sum(excellent) excellent from t group by submission_date,poor,test_type,group_id"
    test_list = json.dumps(__db_fetch_values_dict(query_t), default=decimal_date_default)


    query_pngo = "select id,organization from public.usermodule_organizations where id in "+str(org)
    df = pandas.DataFrame()
    df = pandas.read_sql(query_pngo,connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id,org_name)

    # query_for_chart = "with t as( SELECT username, village_geocode, village_name, union_geocode, union_name, upazilla_geocode, upazilla_name, district_geocode, district_name, group_type, maritial_status, submission_date, test_type, group_id, adolescent_name, id_adolescent, number_obtained,case when number_obtained::int <=5 then 1 else 0 end poor,case when number_obtained::int >=6 and number_obtained::int <=9 then 1 else 0 end good,case when number_obtained::int >=10 then 1 else 0 end excellent FROM public.vw_life_skill_education_test)select test_type,sum(poor) poor,sum(good) good,sum(excellent) excellent from t group by test_type order by test_type"
    df = pandas.DataFrame()
    df = pandas.read_sql(query_for_chart, connection)
    pretest = []
    posttest = []
    if not df.empty:
        if df.test_type.tolist()[0] == '1':
            pretest.append(df.poor.tolist()[0])
            pretest.append(df.good.tolist()[0])
            pretest.append(df.excellent.tolist()[0])
        if df.test_type.tolist()[0] == '2':
            posttest.append(df.poor.tolist()[0])
            posttest.append(df.good.tolist()[0])
            posttest.append(df.excellent.tolist()[0])
        if len(df.test_type.tolist()) > 1 and df.test_type.tolist()[1] == '2':
            posttest.append(df.poor.tolist()[1])
            posttest.append(df.good.tolist()[1])
            posttest.append(df.excellent.tolist()[1])
    return render(request, 'planmodule/test_report.html', {
        'test_list': test_list,'organization':organization,'upazila':upazila,'union':union,'user':user,'posttest':posttest,'pretest':pretest
    })


@login_required
def getTestData(request):
    current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
    if current_user:
        current_user = current_user[0]
    all_organizations = get_recursive_organization_children(current_user.organisation_name, [])
    org_id_list = [org.pk for org in all_organizations]
    org = str(map(int, org_id_list))
    org = org.replace('[', '').replace(']', '').replace(' ','')


    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    upazila = json.loads(request.POST.get('upazila'))
    union = json.loads(request.POST.get('union'))
    pngo = json.loads(request.POST.get('pngo'))
    username = json.loads(request.POST.get('username'))
    group = json.loads(request.POST.get('group'))
    test_type = json.loads(request.POST.get('test_type'))
    marital_status = json.loads(request.POST.get('marital_status'))
    session = json.loads(request.POST.get('session'))

    filter_query = "where  submission_date between '" + str(from_date) + "' and '" + str(to_date) + "'"


    if group != "":
        group = str(map(int, group))
        group = group.replace('[', '').replace(']', '').replace(' ', '')
        filter_query += " and group_type = any(string_to_array('" + str(group) + "',',')) "



    if upazila !="":
        upazila = str(map(int, upazila))
        upazila = upazila.replace('[', '').replace(']', '').replace(' ', '')
        filter_query += " and upazilla_geocode::text = any(string_to_array('" + str(upazila) + "',',')) "
    else:
        query = "select geoid,(select field_type_id from geo_data where id = geoid),(select geocode from geo_data where id = geoid) from usermodule_catchment_area where user_id = "+str(request.user.id)
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        if not df.empty and df.field_type_id.tolist()[0]==88:
            upazila_geocode = df.geocode.tolist()[0]
            filter_query += " and upazilla_geocode = '" + str(upazila_geocode)+"'"
        elif not df.empty and df.field_type_id.tolist()[0]==86:
            district_geocode = df.geocode.tolist()[0]
            filter_query += " and district_geocode = '" + str(district_geocode)+"'"

    if pngo !="":
        pngo = str(map(int,pngo))
        pngo = pngo.replace('[', '').replace(']', '').replace(' ','')
        filter_query += " and pngo_id::text = any(string_to_array('"+str(pngo)+"',',')) "
    else:
        filter_query += " and pngo_id::text = any(string_to_array('"+str(org)+"',',')) "

    if union!="":
        union = str(map(int, union))
        union = union.replace('[', '').replace(']', '').replace(' ', '')
        filter_query += " and union_geocode::text = any(string_to_array('" + str(union) + "',',')) "

    if username!="":
        # print(username)
        username = str(map(str, username))
        # username = json.dumps(username)
        # print(username)
        username = username.replace('[', '').replace(']', '').replace('\'', '')
        # print(username)
        filter_query += " and username = any(string_to_array('" + str(username) + "',',')) "



    if test_type!="":
        test_type = str(map(int, test_type))
        test_type = test_type.replace('[', '').replace(']', '').replace(' ', '')
        filter_query += " and test_type = any(string_to_array('" + str(test_type) + "',',')) "

    if marital_status!="":
        marital_status = str(map(int, marital_status))
        marital_status = marital_status.replace('[', '').replace(']', '').replace(' ', '')
        filter_query += " and maritial_status = any(string_to_array('" + str(marital_status) + "',',')) "
    session_query = ""
    if session!="":
        session = str(map(int, session))
        session = session.replace('[', '').replace(']', '').replace(' ', '')
        session_query += " having count(*)::text = any(string_to_array('" + str(session) + "',','))"

    query = "with t as( SELECT username,(select id user_id from auth_user where username=vw_life_skill_education_test.username), village_geocode, village_name, union_geocode, union_name, upazilla_geocode, upazilla_name, district_geocode, district_name, group_type, maritial_status, submission_date, test_type, group_id, adolescent_name, id_adolescent, number_obtained,case when number_obtained::int <=5 then 1 else 0 end poor,case when number_obtained::int >=6 and number_obtained::int <=9 then 1 else 0 end good,case when number_obtained::int >=10 then 1 else 0 end excellent FROM public.vw_life_skill_education_test "+str(filter_query)+"), t1 as( select group_id,count(*) sessions from vw_grp_reg_sessions  group by group_id "+str(session_query)+")select group_id,case when test_type='1' then 'Pre' else 'Post' end test_type,submission_date,count(adolescent_name) enrolled,sum(poor) poor,sum(good) good,sum(excellent) excellent from t where group_id in (select group_id from t1) group by submission_date,test_type,group_id"
    # print(query)

    test_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    query_for_chart = "with t as( SELECT username, village_geocode, village_name, union_geocode, union_name, upazilla_geocode, upazilla_name, district_geocode, district_name, group_type, maritial_status, submission_date, test_type, group_id, adolescent_name, id_adolescent, number_obtained,case when number_obtained::int <=5 then 1 else 0 end poor,case when number_obtained::int >=6 and number_obtained::int <=9 then 1 else 0 end good,case when number_obtained::int >=10 then 1 else 0 end excellent FROM public.vw_life_skill_education_test "+str(filter_query)+"), t1 as( select group_id,count(*) sessions from vw_grp_reg_sessions  group by group_id "+str(session_query)+")select test_type,sum(poor) poor,sum(good) good,sum(excellent) excellent from t where group_id in (select group_id from t1) group by test_type order by test_type"
    df = pandas.DataFrame()
    df = pandas.read_sql(query_for_chart, connection)
    pretest = []
    posttest = []
    if not df.empty:
        if df.test_type.tolist()[0]=='1':
            pretest.append(df.poor.tolist()[0])
            pretest.append(df.good.tolist()[0])
            pretest.append(df.excellent.tolist()[0])
        if df.test_type.tolist()[0] == '2':
            posttest.append(df.poor.tolist()[0])
            posttest.append(df.good.tolist()[0])
            posttest.append(df.excellent.tolist()[0])
        if  len(df.test_type.tolist())>1 and df.test_type.tolist()[1] == '2':
            posttest.append(df.poor.tolist()[1])
            posttest.append(df.good.tolist()[1])
            posttest.append(df.excellent.tolist()[1])
    return HttpResponse(json.dumps({'test_list':test_list,'posttest':posttest,'pretest':pretest}))


@login_required
def economic_empowerment_report(request):
    current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
    if current_user:
        current_user = current_user[0]

    # fetching all organization recursively of current_user
    all_organizations = get_recursive_organization_children(current_user.organisation_name, [])
    org_id_list = [org.pk for org in all_organizations]
    org = str(map(str, org_id_list))
    org = org.replace('[', '(').replace(']', ')')

    query = "select geoid,(select field_type_id from geo_data where id = geoid),(select geocode from geo_data where id = geoid) from usermodule_catchment_area where user_id = (select id from auth_user where username = '"+str(current_user)+"')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)

    if df.empty:
        query_t = "with t as( select * from plan_mis_report_district_form)select 'Number of adolescents girls trained' as cat_name,coalesce(sum(female_girls_unmarried)+sum(female_girls_married),0) summation from t where activity_id = '164' union all select 'Number of adolescents supported to find employment',coalesce(sum(male_boys_unmarried)+sum(male_boys_married)+sum(female_girls_unmarried)+sum(female_girls_married),0) from t where activity_id = '265' union all select 'Number of adolescents supported for enterprise development',coalesce(sum(male_boys_unmarried)+sum(male_boys_married)+sum(female_girls_unmarried)+sum(female_girls_married),0) from t where activity_id = '366' union all select 'Number of adolescents supported for IT and telemedicine work',coalesce(sum(male_boys_unmarried)+sum(male_boys_married)+sum(female_girls_unmarried)+sum(female_girls_married),0) from t where activity_id = '467'"
        
        query = "select id,field_name from geo_data where field_type_id = 88"
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        upz_id = df.id.tolist()
        upz_name = df.field_name.tolist()
        upazila = zip(upz_id, upz_name)


    elif not df.empty:
        geoid = df.geoid.tolist()[0]
        geocode = df.geocode.tolist()[0]

        if df.field_type_id.tolist()[0] == 86:
            query_t = "with t as( select * from plan_mis_report_district_form where pngo_id in "+str(org)+" and district = "+str(geoid)+")select 'Number of adolescents girls trained' as cat_name,coalesce(sum(female_girls_unmarried)+sum(female_girls_married),0) summation from t where activity_id = '164' union all select 'Number of adolescents supported to find employment',coalesce(sum(male_boys_unmarried)+sum(male_boys_married)+sum(female_girls_unmarried)+sum(female_girls_married),0) from t where activity_id = '265' union all select 'Number of adolescents supported for enterprise development',coalesce(sum(male_boys_unmarried)+sum(male_boys_married)+sum(female_girls_unmarried)+sum(female_girls_married),0) from t where activity_id = '366' union all select 'Number of adolescents supported for IT and telemedicine work',coalesce(sum(male_boys_unmarried)+sum(male_boys_married)+sum(female_girls_unmarried)+sum(female_girls_married),0) from t where activity_id = '467'"
            
            query = "select id,field_name from geo_data where field_type_id = 88"
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            upz_id = df.id.tolist()
            upz_name = df.field_name.tolist()
            upazila = zip(upz_id, upz_name)

        elif df.field_type_id.tolist()[0] == 88:
            query_t = "with t as( select * from plan_mis_report_district_form where pngo_id in "+str(org)+" and upazilla = "+str(geoid)+")select 'Number of adolescents girls trained' as cat_name,coalesce(sum(female_girls_unmarried)+sum(female_girls_married),0) summation from t where activity_id = '164' union all select 'Number of adolescents supported to find employment',coalesce(sum(male_boys_unmarried)+sum(male_boys_married)+sum(female_girls_unmarried)+sum(female_girls_married),0) from t where activity_id = '265' union all select 'Number of adolescents supported for enterprise development',coalesce(sum(male_boys_unmarried)+sum(male_boys_married)+sum(female_girls_unmarried)+sum(female_girls_married),0) from t where activity_id = '366' union all select 'Number of adolescents supported for IT and telemedicine work',coalesce(sum(male_boys_unmarried)+sum(male_boys_married)+sum(female_girls_unmarried)+sum(female_girls_married),0) from t where activity_id = '467'"
            
            query = "select id,field_name from geo_data where field_type_id = 88 and id = "+str(geoid)
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            upz_id = df.id.tolist()
            upz_name = df.field_name.tolist()
            upazila = zip(upz_id, upz_name)

    
    economic_empowerment_list = json.dumps(__db_fetch_values_dict(query_t), default=decimal_date_default)
    df = pandas.DataFrame()
    df = pandas.read_sql(query_t, connection)
    chartvalue = df.summation.tolist()


    query_pngo = "select id,organization from public.usermodule_organizations where id in "+str(org)
    df = pandas.DataFrame()
    df = pandas.read_sql(query_pngo,connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id,org_name)

    return render(request, 'planmodule/economic_empowerment_report.html', {
        'economic_empowerment_list': economic_empowerment_list,'upazila':upazila,'chartvalue':chartvalue,'organization':organization
    })


@login_required
def getEconomicData(request):
    current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
    if current_user:
        current_user = current_user[0]

    # fetching all organization recursively of current_user
    all_organizations = get_recursive_organization_children(current_user.organisation_name, [])
    org_id_list = [org.pk for org in all_organizations]
    org = str(map(str, org_id_list))
    org = org.replace('[', '(').replace(']', ')')

    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    upazila = request.POST.get('upazila')
    pngo = request.POST.get('pngo')
    filter_query = "where  activity_date between '" + str(from_date) + "' and '" + str(to_date) + "'"


    if upazila !="":
        filter_query += " and upazilla = "+str(upazila)
    else:
        query = "select geoid,(select field_type_id from geo_data where id = geoid),(select geocode from geo_data where id = geoid) from usermodule_catchment_area where user_id = "+str(request.user.id)
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        if not df.empty and df.field_type_id.tolist()[0]==88:
            upazila = df.geoid.tolist()[0]
            filter_query += " and upazilla = " + str(upazila)
        elif not df.empty and df.field_type_id.tolist()[0]==86:
            district = df.geoid.tolist()[0]
            filter_query += " and district = " + str(district)
    
    if pngo !="":
        filter_query += " and pngo_id = '"+str(pngo)+"'"
    else:
        filter_query += " and pngo_id in " + str(org)            

    query = "with t as( select * from plan_mis_report_district_form "+str(filter_query)+")select 'Number of adolescents girls trained' as cat_name,coalesce(sum(female_girls_unmarried)+sum(female_girls_married),0) summation from t where activity_id = '164' union all select 'Number of adolescents supported to find employment',coalesce(sum(male_boys_unmarried)+sum(male_boys_married)+sum(female_girls_unmarried)+sum(female_girls_married),0) from t where activity_id = '265' union all select 'Number of adolescents supported for enterprise development',coalesce(sum(male_boys_unmarried)+sum(male_boys_married)+sum(female_girls_unmarried)+sum(female_girls_married),0) from t where activity_id = '366' union all select 'Number of adolescents supported for IT and telemedicine work',coalesce(sum(male_boys_unmarried)+sum(male_boys_married)+sum(female_girls_unmarried)+sum(female_girls_married),0) from t where activity_id = '467'"
    economic_empowerment_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    chartvalue = df.summation.tolist()
    return HttpResponse(json.dumps({'economic_empowerment_list':economic_empowerment_list,'chartvalue':chartvalue}))


@login_required
def dca_list(request):
    current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
    if current_user:
        current_user = current_user[0]

    # fetching all organization recursively of current_user
    all_organizations = get_recursive_organization_children(current_user.organisation_name, [])
    org_id_list = [org.pk for org in all_organizations]
    org = str(map(str, org_id_list))
    org = org.replace('[', '(').replace(']', ')')
    query = "SELECT plan_dca.id, registration_date, COALESCE((select field_name from public.geo_data where id = district),'') district,COALESCE((select field_name from public.geo_data where id = upazilla),'') upazilla,(select activity_name from public.plan_activities where activity_value = activity_id limit 1) activity_name,case when activity_level = 2 then 'District' else 'Central' end activity_level, males, females FROM public.plan_dca,plan_dca_activities where plan_dca.id = plan_dca_activities.plan_dca_id and pngo_id in " + str(org)
    dca_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)

    return render(request, 'planmodule/dca_list.html', {
        'dca_list': dca_list
    })

@login_required
def add_dca_form(request):
    query = "select id,field_name from geo_data where field_type_id = 86"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    dist_id = df.id.tolist()
    dist_name = df.field_name.tolist()
    district = zip(dist_id, dist_name)
    user_id = request.user.id
    query = "select id,organization from public.usermodule_organizations where id = ( select organisation_name_id from public.usermodule_usermoduleprofile where user_id = " + str(
        user_id) + ")"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()[0]
    org_name = df.organization.tolist()[0]
    query = "select * from public.plan_activities where activity_type = 2"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    act_id = df.activity_value.tolist()
    act_name = df.activity_name.tolist()
    activity = zip(act_id, act_name)
    return render(request, 'planmodule/add_dca_form.html',
                  {'district': district, 'org_id': org_id, 'org_name': org_name,'activity':activity})


@login_required
def insert_dca_form(request):
    if request.POST:
        registration_date = request.POST.get('registration_date')
        district = request.POST.get('district')
        upazilla = request.POST.get('upazilla')
        activity_name = request.POST.getlist('activity_name')
        activity_level = request.POST.get('activity_level')
        pngo_id = request.POST.get('org_id')
        males = request.POST.getlist('males')
        females = request.POST.getlist('females')
        if district and upazilla:
            insert_query = "INSERT INTO public.plan_dca (id,registration_date, district, upazilla, pngo_id, activity_level) VALUES(nextval('plan_dca_id_seq'::regclass),'"+str(registration_date)+"', "+str(district)+", "+str(upazilla)+", "+str(pngo_id)+", "+str(activity_level)+") RETURNING id"
        else:
            insert_query = "INSERT INTO public.plan_dca (id,registration_date,  pngo_id, activity_level) VALUES(nextval('plan_dca_id_seq'::regclass),'" + str(
                registration_date) + "',  " + str(pngo_id) + ", " + str(activity_level) + ") RETURNING id"
        id = __db_fetch_single_value(insert_query)
        i = 0
        for each in activity_name:
            q = "INSERT INTO public.plan_dca_activities (plan_dca_id, activity_id, males, females) VALUES("+str(id)+", '"+str(each)+"', "+str(males[i])+", "+str(females[i])+"  )"
            i = i+ 1
            __db_commit_query(q)
        messages.success(request, '<i class="fa fa-check-circle"></i> New DCA has been added successfully!',
                             extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/planmodule/dca_list/")


@login_required
def delete_dca_form(request, dca_id):
    delete_query = "delete from plan_dca where id = " + str(dca_id) + ""
    __db_commit_query(delete_query)
    messages.success(request, '<i class="fa fa-check-circle"></i> DCA has been deleted successfully!',
                             extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/planmodule/dca_list/")


@login_required
def edit_dca_form(request, dca_id):
    query = "SELECT plan_dca.id, registration_date, district,(SELECT field_name FROM PUBLIC.geo_data WHERE id = district) district_name, upazilla, (SELECT field_name FROM PUBLIC.geo_data WHERE id = upazilla) upazilla_name, activity_level FROM PUBLIC.plan_dca  where id=" + str(dca_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    data = {}
    data['dca_id'] = dca_id
    registration_date = df.registration_date.tolist()[0]
    district_id = df.district.tolist()[0]
    district_name = df.district_name.tolist()[0]
    upazilla_id = df.upazilla.tolist()[0]
    upazilla_name = df.upazilla_name.tolist()[0]
    activity_level = df.activity_level.tolist()[0]
    # data['males'] = df.males.tolist()[0]
    # data['females'] = df.females.tolist()[0]

    if district_id is not None:
        query = "select id,field_name from geo_data where field_type_id = 88 and field_parent_id = " + str(district_id)
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        upz_id = df.id.tolist()
        upz_name = df.field_name.tolist()
        upazilla = zip(upz_id, upz_name)
    else:
        query = "select id,field_name from geo_data where field_type_id = 88 "
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        upz_id = df.id.tolist()
        upz_name = df.field_name.tolist()
        upazilla = zip(upz_id, upz_name)


    query = "select id,organization from public.usermodule_organizations where id = (select pngo_id from public.plan_dca where id = " + str(dca_id) + ")"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    org_id = df.id.tolist()[0]
    org_name = df.organization.tolist()[0]

    query = "select * from public.plan_activities where activity_type = 2"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    act_id = df.activity_value.tolist()
    act_name = df.activity_name.tolist()
    activity = zip(act_id, act_name)

    query = "select * from plan_dca_activities where plan_dca_id ="+str(dca_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    set_activity_id = df.activity_id.tolist()
    set_males_number = df.males.tolist()
    set_females_number = df.females.tolist()

    sss = zip(set_activity_id,set_males_number,set_females_number)

    return render(request, 'planmodule/edit_dca_form.html',
                  {'data': json.dumps(data, default=decimal_date_default), 'district_id': district_id,
                   'district_name': district_name, 'upazilla_id': upazilla_id, 'upazilla_name': upazilla_name,
                   'upazilla': upazilla, 'org_id': org_id, 'org_name': org_name,'registration_date':registration_date,'activity_level':activity_level,'activity':activity,"sss":sss})



@login_required
def update_dca_form(request):
    if request.POST:
        dca_id = request.POST.get('dca_id')
        registration_date = request.POST.get('registration_date')
        district = request.POST.get('district')
        upazilla = request.POST.get('upazilla')
        activity_name = request.POST.getlist('activity_name')
        activity_level = request.POST.get('activity_level')
        pngo_id = request.POST.get('org_id')
        males = request.POST.getlist('males')
        females = request.POST.getlist('females')
        delete_query = "delete from plan_dca where id = "+str(dca_id)
        __db_commit_query(delete_query)
        if district and upazilla:
            insert_query = "INSERT INTO public.plan_dca (id,registration_date, district, upazilla, pngo_id, activity_level) VALUES(nextval('plan_dca_id_seq'::regclass),'"+str(registration_date)+"', "+str(district)+", "+str(upazilla)+", "+str(pngo_id)+", "+str(activity_level)+") RETURNING id"
        else:
            insert_query = "INSERT INTO public.plan_dca (id,registration_date,  pngo_id, activity_level) VALUES(nextval('plan_dca_id_seq'::regclass),'" + str(
                registration_date) + "',  " + str(pngo_id) + ", " + str(activity_level) + ") RETURNING id"
        id = __db_fetch_single_value(insert_query)
        i = 0
        for each in activity_name:
            q = "INSERT INTO public.plan_dca_activities (plan_dca_id, activity_id, males, females) VALUES("+str(id)+", '"+str(each)+"', "+str(males[i])+", "+str(females[i])+")"
            i = i+ 1
            __db_commit_query(q)
        messages.success(request, '<i class="fa fa-check-circle"></i> DCA Info has been updated successfully!',
                             extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/planmodule/dca_list/")




@login_required
def mis_report_district_list(request):
    current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
    if current_user:
        current_user = current_user[0]
    # fetching all organization recursively of current_user
    all_organizations = get_recursive_organization_children(current_user.organisation_name, [])
    org_id_list = [org.pk for org in all_organizations]
    org = str(map(str, org_id_list))
    org = org.replace('[', '(').replace(']', ')')

    user_id = request.user.id
    query = "select geoid from public.usermodule_catchment_area where user_id =" + str(user_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    if not df.empty:
        geoid = df.geoid.tolist()[0]
        query = "select field_type_id from geo_data where id =" + str(geoid)
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        field_type_id = df.field_type_id.tolist()[0]
        if field_type_id == 88:
            query = "SELECT id, activity_date, activity_type, CASE WHEN activity_type = 2 THEN 'District Level' ELSE 'Upazilla Level' END activity_type_name, activity_id,(select activity_name from public.plan_activities where activity_value = activity_id limit 1) activity_name, number_of_activity, male_boys_unmarried, male_boys_married, female_girls_unmarried, female_girls_married, comments, pngo_id, (select organization from public.usermodule_organizations where id = pngo_id) pngo_name, district district_id, coalesce((select field_name from geo_data where id = district),'') district_name, upazilla upazilla_id, coalesce((select field_name from geo_data where id = upazilla ),'') upazilla_name FROM plan_mis_report_district_form where activity_type = 3 and upazilla = "+str(geoid)+" and pngo_id in " + str(org)
        else:
            query = "SELECT id, activity_date, activity_type, CASE WHEN activity_type = 2 THEN 'District Level' ELSE 'Upazilla Level' END activity_type_name, activity_id,(select activity_name from public.plan_activities where activity_value = activity_id limit 1) activity_name, number_of_activity, male_boys_unmarried, male_boys_married, female_girls_unmarried, female_girls_married, comments, pngo_id, (select organization from public.usermodule_organizations where id = pngo_id) pngo_name, district district_id, coalesce((select field_name from geo_data where id = district),'') district_name, upazilla upazilla_id, coalesce((select field_name from geo_data where id = upazilla ),'') upazilla_name FROM plan_mis_report_district_form where district is not null and pngo_id in " + str(org)
    else:
        query = "SELECT id, activity_date, activity_type, CASE WHEN activity_type = 2 THEN 'District Level' ELSE 'Upazilla Level' END activity_type_name, activity_id,(select activity_name from public.plan_activities where activity_value = activity_id limit 1) activity_name, number_of_activity, male_boys_unmarried, male_boys_married, female_girls_unmarried, female_girls_married, comments, pngo_id, (select organization from public.usermodule_organizations where id = pngo_id) pngo_name, district district_id, coalesce((select field_name from geo_data where id = district),'') district_name, upazilla upazilla_id, coalesce((select field_name from geo_data where id = upazilla ),'') upazilla_name FROM plan_mis_report_district_form where pngo_id in " + str(org)
    mis_report_district_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return render(request, 'planmodule/mis_report_district_list.html', {
        'mis_report_district_list': mis_report_district_list
    })


@login_required
def community_orientation_list(request):
    current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
    if current_user:
        current_user = current_user[0]
    # fetching all organization recursively of current_user
    all_organizations = get_recursive_organization_children(current_user.organisation_name, [])
    print(all_organizations)
    org_id_list = [org.pk for org in all_organizations]
    org = str(map(str, org_id_list))
    org = org.replace('[', '(').replace(']', ')')
    print(org)
    query = "SELECT DISTINCT ON(data_id) data_id, pngo pngo_name, (SELECT field_name FROM geo_data WHERE geocode = upazila limit 1) AS upazila_name, (SELECT field_name FROM geo_data WHERE geocode = union_name limit 1) AS union_name, date AS orientation_date, CASE orientation_type WHEN '1' THEN 'কমিউনিটি ওরিয়েন্টেশন' WHEN '2' THEN 'ধর্মীয় নেতা'  WHEN '3' THEN  'বিবাহিত কিশোরী / দম্পত্তি ওরিয়েন্টেশন' WHEN '4' THEN 'ইস্যুভিত্তিক মিটিং'  END AS orientation_type FROM vw_comm_orientation where pngo in (select organization from usermodule_organizations where id::text in" + str(org)+" )"
    community_orientation_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return render(request, 'planmodule/community_orientation_list.html', {
        'community_orientation_list': community_orientation_list
    })

@login_required
def delete_community_orientation(request, data_id):
    delete_query = "update logger_instance set deleted_at = now() where xform_id = 564 and id = " + str(data_id)
    __db_commit_query(delete_query)
    messages.success(request, '<i class="fa fa-check-circle"></i> Community Orientation Info has been deleted successfully!',
                             extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/planmodule/community_orientation_list/")


@login_required
def getCommunityData(request):
    orientation_type = request.POST.get('orientation_type')
    pngo = request.POST.get('pngo')
    if orientation_type =="" and pngo=="":
        filter_query = ""
    else:
        filter_query = " where "
    if orientation_type !="":
        filter_query += "orientation_type::int = "+str(orientation_type)
    if pngo !="" and orientation_type !="":
        filter_query += " and pngo = '"+str(pngo)+"'"
    elif pngo!="":
        filter_query += "pngo = '" + str(pngo) + "'"
    query = "SELECT DISTINCT ON(data_id) data_id, pngo pngo_name, (SELECT field_name FROM geo_data WHERE geocode = upazila) AS upazila_name, (SELECT field_name FROM geo_data WHERE geocode = union_name) AS union_name, date AS orientation_date, CASE orientation_type WHEN '1' THEN 'কমিউনিটি ওরিয়েন্টেশন' WHEN '2' THEN 'ধর্মীয় নেতা'  WHEN '3' THEN  'বিবাহিত কিশোরী / দম্পত্তি ওরিয়েন্টেশন' WHEN '4' THEN 'ইস্যুভিত্তিক মিটিং'  END AS orientation_type FROM vw_comm_orientation"+str(filter_query)
    community_orientation_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(community_orientation_list)


@login_required
def add_mis_report_district_form(request):
    user_id = request.user.id
    query = "select geoid from public.usermodule_catchment_area where user_id =" + str(user_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    if df.empty:
        query = "select distinct activity_value,activity_name from public.plan_activities"
    else:
        geoid = df.geoid.tolist()[0]
        query_geo = "select field_type_id from geo_data where id =" + str(geoid)
        df = pandas.DataFrame()
        df = pandas.read_sql(query_geo, connection)
        field_type_id = df.field_type_id.tolist()[0]
        if field_type_id == 86:
            query = "select activity_value,activity_name from public.plan_activities where activity_type = 2"
        elif field_type_id == 88:
            query = "select activity_value,activity_name from public.plan_activities where activity_type = 3"


    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    act_id = df.activity_value.tolist()
    act_name = df.activity_name.tolist()
    activity = zip(act_id, act_name)
    return render(request, 'planmodule/add_mis_report_district_form.html',{'activity':activity})


@login_required
def insert_mis_report_district_form(request):
    if request.POST:
        activity_date = request.POST.get('activity_date')
        activity_id = request.POST.get('activity_name')
        number_of_activity = request.POST.get('number_of_activity')
        male_boys_unmarried = request.POST.get('male_boys_unmarried')
        male_boys_married = request.POST.get('male_boys_married')
        female_girls_unmarried = request.POST.get('female_girls_unmarried')
        female_girls_married = request.POST.get('female_girls_married')
        comments = request.POST.get('comments')

        current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
        if current_user:
            current_user = current_user[0]


        query = "select activity_type from plan_activities where activity_value = '"+str(activity_id)+"' limit 1"
        df = pandas.DataFrame()
        df = pandas.read_sql(query,connection)
        activity_type = df.activity_type.tolist()[0]

        user_id = request.user.id
        pngo_id = current_user.organisation_name_id
        query = "select geoid from public.usermodule_catchment_area where user_id ="+str(user_id)
        df = pandas.DataFrame()
        df = pandas.read_sql(query,connection)
        if df.empty:
            insert_query = "INSERT INTO public.plan_mis_report_district_form(activity_date, activity_type, activity_id, number_of_activity, male_boys_unmarried, male_boys_married, female_girls_unmarried, female_girls_married, comments, pngo_id) VALUES('"+str(activity_date)+"', "+str(activity_type)+", '"+str(activity_id)+"', "+str(number_of_activity)+", "+str(male_boys_unmarried)+", "+str(male_boys_married)+", "+str(female_girls_unmarried)+", "+str(female_girls_married)+",'"+str(comments)+"', "+str(pngo_id)+")"
        else:
            geoid = df.geoid.tolist()[0]
            # print(geoid)
            query = "select field_type_id from geo_data where id ="+str(geoid)
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            field_type_id = df.field_type_id.tolist()[0]
            if field_type_id == 86:
                activity_type = 2
                district = geoid
                insert_query = "INSERT INTO public.plan_mis_report_district_form(activity_date, activity_type, activity_id, number_of_activity, male_boys_unmarried, male_boys_married, female_girls_unmarried, female_girls_married, comments, pngo_id, district) VALUES('" + str(
                activity_date) + "', " + str(activity_type) + ", '" + str(activity_id) + "', " + str(
                number_of_activity) + ", " + str(male_boys_unmarried) + ", " + str(male_boys_married) + ", " + str(
                female_girls_unmarried) + ", " + str(female_girls_married) + ",'" + str(comments) + "', " + str(
                pngo_id) + "," + str(district) + ")"
            elif field_type_id == 88:
                activity_type = 3
                query = "select field_parent_id from geo_data where id =" + str(geoid)
                df = pandas.DataFrame()
                df = pandas.read_sql(query, connection)
                district = df.field_parent_id.tolist()[0]
                upazilla = geoid
                insert_query = "INSERT INTO public.plan_mis_report_district_form(activity_date, activity_type, activity_id, number_of_activity, male_boys_unmarried, male_boys_married, female_girls_unmarried, female_girls_married, comments, pngo_id, district, upazilla) VALUES('" + str(
                activity_date) + "', " + str(activity_type) + ", '" + str(activity_id) + "', " + str(
                number_of_activity) + ", " + str(male_boys_unmarried) + ", " + str(male_boys_married) + ", " + str(
                female_girls_unmarried) + ", " + str(female_girls_married) + ",'" + str(comments) + "', " + str(
                pngo_id) + "," + str(district) + ", " + str(upazilla) + ")"        
        __db_commit_query(insert_query)
        messages.success(request, '<i class="fa fa-check-circle"></i> MIS Info has been added successfully!',
                             extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/planmodule/mis_report_district_list/")



@login_required
def edit_mis_report_district_form(request, mis_report_id):
    query = "SELECT id, activity_date, activity_type, CASE WHEN activity_type = 2 THEN 'District Level' ELSE 'Upazilla Level' END activity_type_name, activity_id,(select activity_name from public.plan_activities where activity_value = activity_id and plan_activities.activity_type = t.activity_type) activity_name, number_of_activity, male_boys_unmarried, male_boys_married, female_girls_unmarried, female_girls_married, comments, pngo_id, (select organization from public.usermodule_organizations where id = pngo_id) pngo_name, district district_id, coalesce((select field_name from geo_data where id = district),'') district_name, upazilla upazilla_id, coalesce((select field_name from geo_data where id = upazilla ),'') upazilla_name FROM plan_mis_report_district_form t where id=" + str(mis_report_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    data = {}
    data['mis_report_id'] = mis_report_id
    data['number_of_activity'] = df.number_of_activity.tolist()[0]
    data['male_boys_unmarried'] = df.male_boys_unmarried.tolist()[0]
    data['male_boys_married'] = df.male_boys_married.tolist()[0]
    data['female_girls_unmarried'] = df.female_girls_unmarried.tolist()[0]
    data['female_girls_married'] = df.female_girls_married.tolist()[0]
    data['comments'] = df.comments.tolist()[0]
    activity_date = df.activity_date.tolist()[0]
    set_activity_id = df.activity_id.tolist()[0]

    user_id = request.user.id
    query = "select geoid from public.usermodule_catchment_area where user_id =" + str(user_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    if df.empty:
        query = "select activity_value,activity_name from public.plan_activities"
    else:
        geoid = df.geoid.tolist()[0]
        query_geo = "select field_type_id from geo_data where id =" + str(geoid)
        df = pandas.DataFrame()
        df = pandas.read_sql(query_geo, connection)
        field_type_id = df.field_type_id.tolist()[0]
        if field_type_id == 86:
            query = "select activity_value,activity_name from public.plan_activities where activity_type = 2"
        elif field_type_id == 88:
            query = "select activity_value,activity_name from public.plan_activities where activity_type = 3"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    act_id = df.activity_value.tolist()
    act_name = df.activity_name.tolist()
    activity = zip(act_id, act_name)
    return render(request, 'planmodule/edit_mis_report_district_form.html',
                  {'data': json.dumps(data, default=decimal_date_default),'activity':activity,'activity_date':activity_date,'set_activity_id':set_activity_id})



@login_required
def update_mis_report_district_form(request):
    if request.POST:
        mis_report_id = request.POST.get('mis_report_id')
        activity_date = request.POST.get('activity_date')
        activity_id = request.POST.get('activity_name')
        number_of_activity = request.POST.get('number_of_activity')
        male_boys_unmarried = request.POST.get('male_boys_unmarried')
        male_boys_married = request.POST.get('male_boys_married')
        female_girls_unmarried = request.POST.get('female_girls_unmarried')
        female_girls_married = request.POST.get('female_girls_married')
        comments = request.POST.get('comments')

        # user_id = request.user.id
        # query = "select geoid from public.usermodule_catchment_area where user_id =" + str(user_id)
        # df = pandas.DataFrame()
        # df = pandas.read_sql(query, connection)

        # if df.empty:


        # query = "select activity_type from plan_activities where activity_value = '"+str(activity_id)+"'"
        # df = pandas.DataFrame()
        # df = pandas.read_sql(query,connection)
        # activity_type = df.activity_type.tolist()[0]
        # activity_type="+str(activity_type)+",
        update_query = "UPDATE public.plan_mis_report_district_form SET activity_date='"+str(activity_date)+"',  activity_id='"+str(activity_id)+"', number_of_activity="+str(number_of_activity)+", male_boys_unmarried="+str(male_boys_unmarried)+", male_boys_married="+str(male_boys_married)+", female_girls_unmarried="+str(female_girls_unmarried)+", female_girls_married="+str(female_girls_married)+", comments='"+str(comments)+"' WHERE id="+str(mis_report_id)
        __db_commit_query(update_query)
        messages.success(request, '<i class="fa fa-check-circle"></i> MIS Info has been updated successfully!',
                             extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/planmodule/mis_report_district_list/")


@login_required
def delete_mis_report_district_form(request, mis_report_id):
    delete_query = "delete from plan_mis_report_district_form where id = " + str(mis_report_id) + ""
    __db_commit_query(delete_query)
    messages.success(request, '<i class="fa fa-check-circle"></i> MIS Info has been deleted successfully!',
                             extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect("/planmodule/mis_report_district_list/")

import simplejson
from onadata.apps.planmodule.forms import FileShareForm

def getAjaxMessage(type, message):
    data = {}
    data['type'] = type
    data['messages'] = message
    return data


@login_required
def file_share(request):
    cntrl_remove_btn = 1
    form = FileShareForm()
    if request.method == 'POST':
        form = FileShareForm(request.POST, request.FILES)
        des = ''
        if form.is_valid():
            title = request.POST.get('title')
            document_type = request.POST.get('document_type')
            des = upload_shared_file(request.FILES['shared_file'],title)
            current_user = request.user.id
            created_date = datetime.datetime.today().strftime('%Y-%m-%d')
            #insert_query = "INSERT INTO public.narrative_report_data ( month_year, ngo, id, file_path) VALUES ( '"+month+"', '"+ngo+"', DEFAULT , '"+des+"');	"
            insert_query = "INSERT INTO public.file_shared ( created_date, shared_file, user_id, id, title,document_type) VALUES ( '"+created_date+"', '"+des+"', "+str(current_user)+", DEFAULT, '"+title+"','"+document_type+"');"
            # print insert_query
            __db_commit_query(insert_query)
            data = getAjaxMessage("success",
                                        "<i class='fa fa-check-circle'> </i>  data has been uploaded successfully.")
        else:
            #print form.as_p()
            # Form is not valid, Send Error message with Form
            return render(request, "eyfw/file_shared/file_share_form.html", {'form': form,'cntrl_remove_btn':cntrl_remove_btn},status=500)
        return HttpResponse(simplejson.dumps(data), content_type="application/json")

    return render(request, "eyfw/file_shared/file_share.html", {'form': form,'cntrl_remove_btn':cntrl_remove_btn})


def upload_shared_file(file,title):
    if file:
        #get system time in miliseconds
        millis = int(round(time.time() * 1000))
        filePath = title+'_'+str(millis)+'_'+str(file.name).replace(' ','_')
        destination = open('onadata/media/shared_file/'+filePath, 'w+')
        for chunk in file.chunks():
            destination.write(chunk)
        destination.close()

    return filePath


@login_required
def getSharedFileList(request):
    cntrl_remove_btn = request.POST.get('cntrl_remove_btn')
    data_query = "select *,(select first_name || ' ' || last_name from auth_user where id= user_id limit 1)  as username from file_shared order by id desc "
    data = __db_fetch_values_dict(data_query)
    data_list = []
    data_dict = {}
    for tmp in data:
        data_dict['id'] = tmp['id']
        data_dict['title'] = tmp['title']
        data_dict['created_date'] = tmp['created_date']
        data_dict['document_type'] = tmp['document_type']
        data_dict['shared_file'] = tmp['shared_file']
        data_dict['username'] = tmp['username']
        data_list.append(data_dict.copy())
        data_dict.clear()

    return render(request, "eyfw/file_shared/file_shared_datalist.html", {'dataset': data_list,'cntrl_remove_btn':cntrl_remove_btn})


@login_required
def delete_sharedFile_data(request,id):
    select_query = "select shared_file from  file_shared where id = "+str(id)
    df = pandas.DataFrame
    df = pandas.read_sql(select_query,connection)
    file_name = df.shared_file.tolist()[0]
    path = 'onadata/media/shared_file/'+str(file_name)
    os.remove(path)

    delete_query = "delete from public.file_shared where id = " + id
    __db_commit_query(delete_query)


    data = getAjaxMessage("success",
                                "<i class='fa fa-check-circle'> </i> Data has been deleted successfully.")

    return HttpResponse(simplejson.dumps(data), content_type="application/json")


@login_required
def shared_file_list(request):
    cntrl_remove_btn = 0
    return render(request, "eyfw/file_shared/shared_file_list.html",{'cntrl_remove_btn':cntrl_remove_btn})


@login_required
def analysis_report(request):
    current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
    if current_user:
        current_user = current_user[0]

    # fetching all organization recursively of current_user
    all_organizations = get_recursive_organization_children(current_user.organisation_name, [])
    org_id_list = [org.pk for org in all_organizations]
    org = str(map(int, org_id_list))
    org = org.replace('[', '').replace(']', '')

    query = "select geoid,(select field_type_id from geo_data where id = geoid),(select geocode from geo_data where id = geoid) from usermodule_catchment_area where user_id = (select id from auth_user where username = '" + str(
        current_user) + "')"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)

    if df.empty:
        query_t = "select * from get_analysis_report('','')"

    elif not df.empty:
        geoid = df.geoid.tolist()[0]
        geocode = df.geocode.tolist()[0]
        if df.field_type_id.tolist()[0] == 86:
            query_t = "select * from get_analysis_report('" + str(org) + "','')"

        elif df.field_type_id.tolist()[0] == 88:
            query_t = "select * from get_analysis_report('" + str(org) + "','" + str(geocode) + "')"

    # csa_list = json.dumps(__db_fetch_values_dict(query_t), default=decimal_date_default)

    df = pandas.DataFrame()
    df = pandas.read_sql(query_t, connection)

    if not df.empty:
        # print df
        # print "DF Pivot table"
        # print df.pivot_table(values='part_num', rows=['session_order', 'sid'], cols='group_type')
        df = df.pivot(index='sid', columns='group_type', values='part_num').reset_index()
        col_list = list(df)
        col_list.remove('sid')
        # print col_list
        if not '1' in col_list:
            df['1'] = '0'
        if not '2' in col_list:
            df['2'] = '0'
        if not '3' in col_list:
            df['3'] = '0'
        if not '4' in col_list:
            df['4'] = '0'
        df['total'] = df[col_list].sum(axis=1)

        df = df.sort(columns='sid', ascending=True, axis=0)
        # print df
        # print df[col_list].sum(axis=0)

        df1 = pandas.DataFrame([['Total', df['1'].sum(axis=0), df['2'].sum(axis=0), df['3'].sum(axis=0),
                                 df['4'].sum(axis=0), df['total'].sum(axis=0)]], columns=list(df))
        df = df.append(df1, ignore_index=True).fillna('')
        df['sid'].replace(1, 'Attended one session', inplace=True)
        df['sid'].replace(2, 'Attended two session', inplace=True)
        df['sid'].replace(3, 'Attended three session', inplace=True)
        df['sid'].replace(4, 'Attended four session', inplace=True)
        df['sid'].replace(5, 'Attended five session', inplace=True)
        df['sid'].replace(6, 'Attended six session', inplace=True)
        df['sid'].replace(7, 'Attended seven session', inplace=True)
        df['sid'].replace(8, 'Attended eight session', inplace=True)

        analysis_list = json.dumps(df.to_dict('list'))

    return render(request, 'planmodule/analysis_report.html', {
        'analysis_list': analysis_list
    })


def edit_community_orientation(request, instance_id):
    id_string = 'community_orientation'
    xform_id = __db_fetch_single_value("select id from logger_xform where id_string ='" + str(id_string) + "'")
    form_uuid = __db_fetch_single_value("select uuid from logger_xform where id = " + str(xform_id))
    xml_data = __db_fetch_single_value("select xml from logger_instance where id = " + str(instance_id))
    xml_data = str(xml_data).replace('\t', '').replace('\n', '').replace("'","\\'")
    username = request.user.username
    return render(request, "planmodule/commnity_orientation.html",
                  {'id_string': id_string, 'xform_id': xform_id, 'username': username,
                   'form_uuid': form_uuid, 'xml_data': xml_data, 'instance_id': instance_id})