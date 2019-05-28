#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import OrderedDict
import datetime
import os
import csv
import xml.etree.ElementTree as ET
import dateutil.parser
import requests

import simplejson as json
import pandas as pd
import pandas

from django.http import HttpResponse
from django.db import connection
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.contrib import messages


def __db_fetch_values(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetch_val = cursor.fetchall()
    cursor.close()
    return fetch_val


def __db_fetch_single_value(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetch_val = cursor.fetchone()
    cursor.close()
    return fetch_val[0]


def __db_commit_query(query):
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    fetch_val = cursor.fetchone()
    cursor.close()
    return fetch_val[0]


def __db_fetch_values_dict(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetch_val = dictfetchall(cursor)
    cursor.close()
    return fetch_val


def __db_commit_query_void(query):
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    cursor.close()


def dictfetchall(cursor):
    desc = cursor.description
    return [
        OrderedDict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()]


# background process
def register_household_adolescent(request):
    unregistered_households = __db_fetch_values_dict(
        "select * from logger_instance where xform_id = 549 and deleted_at is NULL and id::text not in (select sub_id::text from plan_household_profile)")
    for unregistered_hh in unregistered_households:
        hh_id = register_household(unregistered_hh)
        if hh_id:
            register_hh_persons(unregistered_hh, hh_id)
            register_adolescents(unregistered_hh, hh_id)
    return HttpResponse("OK")


def register_household(unregistered_hh):
    district = unregistered_hh['json']['district']
    upazila = unregistered_hh['json']['upazila']
    union_name = unregistered_hh['json']['union_name']
    # mouza = unregistered_hh['json']['mouza']
    village = unregistered_hh['json']['village']
    para = unregistered_hh['json']['para']
    hh_no = unregistered_hh['json']['hh_no']
    hh_head = unregistered_hh['json']['hh_head']
    respondent_name = unregistered_hh['json']['respondent_name']
    ethnicity = unregistered_hh['json']['ethnicity']
    hh_member = unregistered_hh['json']['hh_member']
    member_aged_8_19y = unregistered_hh['json']['member_aged_8_19y']
    sub_id = unregistered_hh['id']
    if unregistered_hh['json'].has_key('_geolocation'):
        latitude = unregistered_hh['json']['_geolocation'][0]
        longitude = unregistered_hh['json']['_geolocation'][1]
    else:
        latitude = 'NULL'
        longitude = 'NULL'
    created_at = dateutil.parser.parse(unregistered_hh['json']['_submission_time'])
    created_user = User.objects.filter(username=unregistered_hh['json']['_submitted_by'])
    pngo_id = unregistered_hh['json']['pngo']

    hh_id = __db_commit_query(
        "INSERT INTO public.plan_household_profile (id, district, upazila, union_name, mouza, village, para, hh_no, hh_head, respondent_name, ethnicity, hh_member, member_aged_8_19y, latitude, longitude, pngo_id, created_at, created_by, updated_at, updated_by,sub_id) VALUES(nextval('plan_household_profile_id_seq'::regclass), " + str(
            district) + ", " + str(upazila) + ", " + str(union_name) + ", 0, " + str(
            village) + ", " + str(para) + ", '" + str(hh_no) + "', '" + str(
            hh_head) + "', '" + respondent_name + "', " + str(ethnicity) + ", " + str(hh_member) + ", " + str(
            member_aged_8_19y) + ", '" + str(latitude) + "', '" + str(longitude) + "', '" + str(pngo_id) + "', '" + str(
            created_at) + "', " + str(created_user[0].id) + ", NULL, NULL, " + str(sub_id) + ") returning id")

    return hh_id


def register_hh_persons(unregistered_hh, hh_id):
    person_map = [[1, 'mem_name/father_name'], [2, 'mem_name/mother_name'], [3, 'mem_name/husband_wife_name'],
                  [4, 'mem_name/father_in_law'], [5, 'mem_name/mother_in_law']]
    for pm in person_map:
        if unregistered_hh['json'].has_key(pm[1]):
            __db_commit_query(
                "INSERT INTO public.plan_hh_living_person (id, hh_id, person_name, person_type) VALUES(nextval('plan_hh_living_person_id_seq'::regclass), " + str(
                    hh_id) + ", '" + str(unregistered_hh['json'][pm[1]]) + "', " + str(pm[0]) + ") returning id")
    return 0


def register_adolescents(unregistered_hh, hh_id):
    for ado_info in unregistered_hh['json']['ado_info']:
        if not str(ado_info['ado_info/id_adolescent']).endswith('0'):
            adolescent_name = ado_info['ado_info/adolescent_name']
            id_adolescent = ado_info['ado_info/id_adolescent']
            sex = ado_info['ado_info/sex']
            age = ado_info['ado_info/age']
            have_birth_reg = ado_info['ado_info/have_birth_reg']
            have_birth_reg = ado_info['ado_info/have_birth_reg']
            relation = ado_info['ado_info/relation']
            going_school = ado_info['ado_info/going_school']
            work_wage = ado_info['ado_info/work_wage']
            disable = ado_info['ado_info/disable']
            mobile = ado_info['ado_info/mobile']
            mobile_owner = ado_info['ado_info/mobile_owner']
            maritial_status = ado_info['ado_info/maritial_status']
            if ado_info.has_key('marriage_reg'):
                marriage_reg = ado_info['ado_info/marriage_reg']
            else:
                marriage_reg = 'NULL'
            if ado_info.has_key('maritial_duration'):
                maritial_duration = ado_info['ado_info/maritial_duration']
            else:
                maritial_duration = 'NULL'
            if ado_info.has_key('child_any'):
                child_any = ado_info['ado_info/child_any']
            else:
                child_any = 'NULL'
            if ado_info.has_key('child_num'):
                child_num = ado_info['ado_info/child_num']
            else:
                child_num = 'NULL'
            if ado_info.has_key('pregnant_currently'):
                pregnant_currently = ado_info['ado_info/pregnant_currently']
            else:
                pregnant_currently = 'NULL'

            __db_commit_query(
                "INSERT INTO public.plan_adolescents_profile (id, hh_id, adolescent_name, id_adolescent, sex, age, have_birth_reg, relation, going_school, work_wage, disable, mobile, mobile_owner, maritial_status, marriage_reg, maritial_duration, child_any, child_num, pregnant_currently) VALUES(nextval('plan_adolescents_profile_id_seq'::regclass), " + str(
                    hh_id) + ", '" + str(adolescent_name) + "', '" + str(id_adolescent) + "', " + str(sex) + ", " + str(
                    age) + ", " + str(have_birth_reg) + "," + str(relation) + ", " + str(going_school) + ", " + str(
                    work_wage) + ", " + str(disable) + ", '" + str(mobile) + "', " + str(mobile_owner) + ", " + str(
                    maritial_status) + ", " + str(marriage_reg) + "," + str(maritial_duration) + ", " + str(
                    child_any) + ", " + str(child_num) + ", " + str(pregnant_currently) + ") returning id")
    return 0


@csrf_exempt
def get_adolescent_list(request):
    username = request.GET.get('username')
    adolescent_query = "WITH w AS(WITH t AS( SELECT id AS aid, hh_id, adolescent_name, id_adolescent, sex, age, have_birth_reg, relation, going_school, work_wage, disable, mobile, mobile_owner, maritial_status, marriage_reg, maritial_duration, child_any, child_num, pregnant_currently,birth_place,date_birth FROM plan_adolescents_profile), s AS ( SELECT id, district, (select field_name from geo_data where geocode = district::text limit 1) as district_label, upazila, (select field_name from geo_data where geocode = upazila::text limit 1) as upazila_label, union_name, (select field_name from geo_data where geocode = union_name::text limit 1) as union_name_label, mouza, village, (select field_name from geo_data where geocode = village::text limit 1) as village_label, para, (select field_name from geo_data where geocode = para::text limit 1) as para_label, hh_head, hh_no, pngo_id FROM plan_household_profile) SELECT * FROM t, s WHERE t.hh_id = s.id) SELECT DISTINCT ON ( id_adolescent) aid, pngo_id, district, district_label, upazila, upazila_label, union_name, union_name_label, mouza, village, village_label, para, para_label, hh_head, hh_no, adolescent_name, id_adolescent, sex, case sex when 1 then 'Male' when '2' then 'Female' end as sex_label, age, have_birth_reg, relation, going_school, work_wage, disable, mobile, mobile_owner, maritial_status, marriage_reg, maritial_duration, child_any, child_num, pregnant_currently,date_birth,birth_place, ( SELECT person_name FROM plan_hh_living_person WHERE person_type = 1 AND hh_id = w.hh_id limit 1) AS father_name, ( SELECT person_name FROM plan_hh_living_person WHERE person_type = 2 AND hh_id = w.hh_id limit 1) AS mother_name, ( SELECT person_name FROM plan_hh_living_person WHERE person_type = 3 AND hh_id = w.hh_id limit 1) AS husband_wife_name, ( SELECT person_name FROM plan_hh_living_person WHERE person_type = 4 AND hh_id = w.hh_id limit 1) AS father_in_law_name, ( SELECT person_name FROM plan_hh_living_person WHERE person_type = 5 AND hh_id = w.hh_id limit 1) AS mother_in_law_name FROM w WHERE union_name :: text IN ( SELECT ( SELECT geocode FROM geo_data WHERE id = geoid) FROM usermodule_catchment_area WHERE user_id = ( SELECT id FROM auth_user WHERE username = '" + str(
        username) + "'))"
    adolescent_data = __db_fetch_values_dict(adolescent_query)
    return HttpResponse(json.dumps(adolescent_data))


@csrf_exempt
def get_cmp_list(request):
    username = request.GET.get('username')
    cmp_query = "SELECT data_id, pngo, district,(select field_name from geo_data where geocode = district::text limit 1) as district_label, upazila,(select field_name from geo_data where geocode = upazila::text limit 1) as upazila_label, union_name,(select field_name from geo_data where geocode = union_name::text limit 1) as union_name_label, mouza, village,(select field_name from geo_data where geocode = village::text limit 1) as village_label, para,(select field_name from geo_data where geocode = para::text limit 1) as para_label, adolescent_name, id_adolescent, sex, father_name, mother_name, date_birth, birth_place, birth_reg, date_child_marriage_prevented, date_proposed_marriage, person_involved_prevent, username,(select case status when '2' then 'Married' when '1' then 'Unmarried' end as status from vw_plan_vigilance where id_adolescent = vcr.id_adolescent and follow_up_type::int = 1 limit 1) as vigilance_one_mon,(select case status when '2' then 'Married' when '1' then 'Unmarried' end as status from vw_plan_vigilance where id_adolescent = vcr.id_adolescent and follow_up_type::int = 2 limit 1) as vigilance_three_mon,(select case status when '2' then 'Married' when '1' then 'Unmarried' end as status from vw_plan_vigilance where id_adolescent = vcr.id_adolescent and follow_up_type::int = 3 limit 1) as status_at_eighteen FROM public.vw_cmp_registration vcr where union_name :: text IN (SELECT (SELECT geocode FROM geo_data WHERE id = geoid) FROM usermodule_catchment_area WHERE user_id = (SELECT id FROM auth_user WHERE username = '" + str(
        username) + "'))"
    cmp_data = __db_fetch_values_dict(cmp_query)
    return HttpResponse(json.dumps(cmp_data))


@csrf_exempt
def get_lse_group_list(request):
    username = request.GET.get('username')
    lse_grp_list_query = "SELECT row_number() OVER () as serial_no,data_id as group_id ,group_name,pngo, district, upazila, union_name, mouza, village, para,(select field_name from geo_data where geocode = district::text limit 1) as district_label, (select field_name from geo_data where geocode = upazila::text limit 1) as upazila_label, (select field_name from geo_data where geocode = union_name::text limit 1) as union_name_label, (select field_name from geo_data where geocode = village::text limit 1) as village_label, (select field_name from geo_data where geocode = para::text limit 1) as para_label, group_no, group_type,case group_type when '1' then '10-14 yr boys' when '2' then '10-14 yr girls' when '3' then '15-19 yr boys' when '4' then '15-19 yr girls' end as group_type_label,maritial_status,case maritial_status when '1'then 'Unmarried' when '2' then 'Married' end as maritial_status_label, username,(select count(*) from vw_grp_reg_sessions where group_id::int = vw_grp_registration.data_id) as no_of_sessions,((with t as(select group_id, unnest(string_to_array(adolescent_name, ' ')) as adolescent_name from vw_lse_grp_members) select count(*) from t where group_id::int = vw_grp_registration.data_id)) as no_of_adols,(select count(*) from vw_life_skill_education_test where test_type::int = 1 and group_id::int = data_id) as no_of_pre_test FROM public.vw_grp_registration where union_name :: text IN (SELECT (SELECT geocode FROM geo_data WHERE id = geoid) FROM usermodule_catchment_area WHERE user_id = (SELECT id FROM auth_user WHERE username = '" + str(
        username) + "'))"
    lse_grp_list_data = __db_fetch_values_dict(lse_grp_list_query)
    return HttpResponse(json.dumps(lse_grp_list_data))


@csrf_exempt
def get_comm_orientation_list(request):
    username = request.GET.get('username')
    comm_orientation_query = "SELECT data_id,row_number() OVER () as serial_no, date, case orientation_type When '1' then 'কমিউনিটি ওরিয়েন্টেশন' When '2' then 'ধর্মীয় নেতা' When '3' then 'বিবাহিত কিশোরী / দম্পত্তি ওরিয়েন্টেশন' When '4' then 'ইস্যুভিত্তিক মিটিং' end as orientation_type, count(data_id) as no_of_participants FROM public.vw_comm_orientation where union_name :: text IN (SELECT (SELECT geocode FROM geo_data WHERE id = geoid) FROM usermodule_catchment_area WHERE user_id = (SELECT id FROM auth_user WHERE username = '" + str(
        username) + "')) group by data_id,orientation_type,date order by date(date) DESC"
    comm_orientation_data = __db_fetch_values_dict(comm_orientation_query)
    return HttpResponse(json.dumps(comm_orientation_data))


@csrf_exempt
def get_csa_list(request):
    username = request.GET.get('username')
    csa_list_query = "select data_id, vcr.id_adolescent,(select adolescent_name from plan_adolescents_profile where id_adolescent = vcr.id_adolescent limit 1) as adolescent_name,to_char(business_start_month::date, 'Mon YYYY') as business_start_month from vw_csa_registration vcr where vcr.union_name :: text IN (SELECT (SELECT geocode FROM geo_data WHERE id = geoid) FROM usermodule_catchment_area WHERE user_id = (SELECT id FROM auth_user WHERE username = '" + str(
        username) + "'))"
    csa_list_data = __db_fetch_values_dict(csa_list_query)
    return HttpResponse(json.dumps(csa_list_data))


@csrf_exempt
def get_adolescent_list_by_group(request):
    group_id = request.GET.get('group_id')
    # adolescent_list_query = "with t as(select group_id, unnest(string_to_array(adolescent_name, ' ')) as id_adolescent from vw_lse_grp_members) select t.id_adolescent,(select adolescent_name from plan_adolescents_profile where id_adolescent = t.id_adolescent) as adolescent_name from t where group_id::int = "+str(group_id)
    # adolescent_list_data = __db_fetch_values_dict(adolescent_list_query)
    # return HttpResponse(json.dumps(adolescent_list_data))

    curated_data = []

    adolescent_without_sessions = __db_fetch_values_dict(
        "with k as(with t as(select Unnest(String_to_array(adolescent_name, ' ')) as id_adolescent from vw_lse_grp_members where group_id::int = " + str(
            group_id) + "), s as(select id_adolescent from vw_grp_all_sessions where group_id::int = " + str(
            group_id) + " and group_id != 'N/A') select * from t except(select * from s)) select id_adolescent,(SELECT adolescent_name FROM   plan_adolescents_profile WHERE  id_adolescent = k.id_adolescent limit 1) as adolescent_name from k")

    regular_sessions = __db_fetch_values_dict(
        "select distinct session from vw_grp_reg_sessions where group_id::int = " + str(group_id))
    # print adolescent_without_sessions
    # print regular_sessions

    group_attendance_data = __db_fetch_values_dict(
        "WITH v AS(WITH t AS( SELECT session_date, group_id, Unnest(String_to_array(adolescent_name, ' ')) AS id_adolescent, session, '1' AS session_type FROM vw_grp_reg_sessions UNION ALL SELECT session_date, group_id, Unnest(String_to_array(adolescent_name, ' ')) AS id_adolescent, session, '2' AS session_type FROM vw_grp_mkp_sessions) SELECT DISTINCT ON ( id_adolescent,session) * FROM t), n AS(WITH m AS ( SELECT group_id, Unnest(String_to_array(adolescent_name, ' ')) AS id_adolescent FROM vw_lse_grp_members) SELECT m.id_adolescent, m.group_id, ( SELECT adolescent_name FROM plan_adolescents_profile WHERE id_adolescent = m.id_adolescent limit 1) AS adolescent_name FROM m) SELECT n.id_adolescent, ( SELECT adolescent_name FROM plan_adolescents_profile WHERE id_adolescent = n.id_adolescent limit 1) AS adolescent_name, session, session_type FROM v, n WHERE v.group_id = n.group_id AND v.id_adolescent = n.id_adolescent AND v.group_id::int = " + str(
            group_id) + " union all (with h as(select group_id,unnest(string_to_array(adolescent_name, ' ')) as id_adolescent from vw_lse_grp_members where group_id is not null and group_id not in (select distinct group_id from vw_grp_reg_sessions union select distinct group_id from vw_grp_mkp_sessions) and group_id::int = " + str(
            group_id) + ") select h.id_adolescent,(select adolescent_name from plan_adolescents_profile where id_adolescent = h.id_adolescent limit 1) as adolescent_name,0::text as session,null as session_type from h)")

    # group_all_session_list = list(sum(__db_fetch_values("with q as( select json_array_elements((json::json->'choices')->'session') as choices from logger_xform where id = 558) select choices->>'name' as name from q where choices->>'myfilter' =(select group_type from vw_grp_registration where data_id = " + str(group_id) + ")"), ()))

    group_all_session_list = __db_fetch_values(
        "select distinct session::text from vw_grp_reg_sessions where group_id::int = " + str(group_id) + "")

    group_all_session_list = list(sum(group_all_session_list, ()))

    adolescent_sessions = {}
    listed_adols = []
    for gad in group_attendance_data:
        if not adolescent_sessions.has_key(gad['id_adolescent']):
            adolescent_sessions[gad['id_adolescent']] = [{gad['session']: gad['session_type']}]
        else:
            adolescent_sessions[gad['id_adolescent']].append({gad['session']: gad['session_type']})

    for adol in adolescent_sessions:
        sessions = []
        for gasl in group_all_session_list:
            if gasl in [y for x in [s.keys() for s in adolescent_sessions[adol]] for y in x]:
                merged_sessions = {}
                for k in adolescent_sessions[adol]:
                    merged_sessions.update(k)
                sessions_type = merged_sessions[gasl]
                if sessions_type == '1':
                    sessions.append({'sessions': gasl, 'is_present': 1})
                else:
                    sessions.append({'sessions': gasl, 'is_present': 2})
            else:
                sessions.append({'sessions': gasl, 'is_present': 0})

        ################################################################

        if adol not in listed_adols:
            listed_adols.append(adol)
            new_od = [d for d in group_attendance_data if d['id_adolescent'] == adol][0]
            del new_od['session']
            del new_od['session_type']
            new_od.update({'sessions': sessions})
            curated_data.append(new_od)

    for aws in adolescent_without_sessions:
        aws_dict = {}
        session_details_outer = []
        for grs in regular_sessions:
            session_details = {}
            session_details['sessions'] = grs['session']
            session_details['is_present'] = 0
            session_details_outer.append(session_details)
        aws_dict['sessions'] = session_details_outer
        aws_dict['adolescent_name'] = aws['adolescent_name']
        aws_dict['id_adolescent'] = aws['id_adolescent']
        curated_data.append(aws_dict)

    return HttpResponse(json.dumps(curated_data))


@csrf_exempt
def get_monthly_cf_form_list(request):
    username = request.GET.get('username')
    monthly_cf_query = "SELECT data_id, activity_date, activity_name,CASE activity_name WHEN 'IR2_3B_26' THEN 'Provide Orientation to Positive Deviant Married Adolescents Couple' WHEN 'IR2_3B_27' THEN 'Positive deviant married adolescents engaged to share their life experience.' WHEN 'IR2_4A_30' THEN 'Adolescents visited health facilities through exposure visits arranged by A2H.' WHEN 'IR3_2C_42' THEN 'Distribute Information pocket card on ASRH information and services' WHEN 'IR3_3D_48' THEN 'Review sessions held for assessing AFHS at the facilities (using Community Score Card)' WHEN 'IR3_3E_492' THEN 'Meeting held with the stakeholders at USHEFP committee' WHEN 'IR3_3E_493' THEN 'Meeting held with the stakeholders at FWC & CC committee' WHEN 'IR3_3F_51' THEN 'School based sessions organized by Guest speakers' WHEN 'IR3_3F_52' THEN 'Adolescents attended sessions organized by guest speakers' WHEN 'IR3_3F_53' THEN 'School based sessions organized by trained teachers' WHEN 'IR3_3F_54' THEN 'Adolescents attended sessions organized by trained teachers' END AS activity_label, ir3_3d_48, no_of_activity, ir3_2c_42, male_married, male_unmarried, female_married, female_unmarried, boy_10_14_married, boy_10_14_unmarried, girl_10_14_married, girl_10_14_unmarried, boy_15_19_married, boy_15_19_unmarried, girl_15_19_married, girl_15_19_unmarried, comments, username FROM public.vw_cf_miscellaneous_activity where username = '" + str(
        username) + "'"
    monthly_cf_data = __db_fetch_values_dict(monthly_cf_query)
    return HttpResponse(json.dumps(monthly_cf_data))


@csrf_exempt
def get_session_list_group(request):
    group_id = request.GET.get('group_id')
    session_list_query = "select session as sess_name,session_label as sess_label from vw_grp_reg_sessions where group_id::int = " + str(
        group_id)
    session_list_data = __db_fetch_values(session_list_query)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="' + str(group_id) + '_sessions.csv"'
    writer = csv.writer(response)
    writer.writerow(['sess_name', 'sess_label'])
    for data in session_list_data:
        writer.writerow([data[0].encode('utf-8'), data[1].encode('utf-8')])
    return response


@csrf_exempt
def get_makeup_session_data(request):
    group_id = request.GET.get('group_id')
    makeup_session_query = "with f as(WITH g AS(WITH k AS(WITH m AS( SELECT Unnest(String_to_array(adolescent_name,' ')) AS adolescent_name FROM vw_lse_grp_members WHERE group_id::int = " + str(
        group_id) + "), n AS(WITH t AS ( SELECT Json_array_elements(json::json->'choices'->'session') AS sessions_list FROM logger_xform WHERE id = 558) SELECT sessions_list->>'name' AS session_no FROM t WHERE sessions_list->>'myfilter' = ( SELECT group_type FROM vw_grp_registration WHERE data_id::int = " + str(
        group_id) + ")) SELECT session_no AS sessionid, adolescent_name AS adolescentid FROM m, n), q AS (WITH t AS ( SELECT session, Unnest(String_to_array(adolescent_name,' ')) AS adolescent_name FROM vw_grp_reg_sessions WHERE group_id::int = " + str(
        group_id) + " UNION ALL SELECT session, unnest(string_to_array(adolescent_name,' ')) AS adolescent_name FROM vw_grp_mkp_sessions WHERE group_id::int = " + str(
        group_id) + ") SELECT DISTINCT session AS sessionid, adolescent_name AS adolescentid FROM t) SELECT * FROM k EXCEPT ( SELECT * FROM q)) SELECT ( SELECT label FROM vw_sessions_list WHERE NAME = sessionid limit 1) AS sessionname, sessionid, ( SELECT adolescent_name FROM plan_adolescents_profile WHERE id_adolescent = adolescentid limit 1) AS adolescent, adolescentid FROM g) select * from f where f.sessionid in (select session from vw_grp_reg_sessions where group_id::int = " + str(
        group_id) + ")"
    makeup_session_data = __db_fetch_values(makeup_session_query)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="' + str(group_id) + '_makeup_sessions.csv"'
    writer = csv.writer(response)
    writer.writerow(['sessionname', 'sessionid', 'adolescent', 'adolescentid'])
    for data in makeup_session_data:
        writer.writerow(
            [data[0].encode('utf-8'), data[1].encode('utf-8'), data[2].encode('utf-8'), data[3].encode('utf-8')])
    return response


@csrf_exempt
def get_geolocation_csv(request):
    username = request.GET.get('username')
    geolocation_query = "with f as (with g as(with n as(with m as(with t as(select geoid from usermodule_catchment_area where user_id =(select id from auth_user where username = '" + str(
        username) + "')), s as (select * from geo_data) select t.geoid,s.field_name,s.geocode,s.field_parent_id from t,s where s.id = t.geoid) select (select field_parent_id from geo_data where id = m.field_parent_id) as field_parent_id,(select geocode from geo_data where id = m.field_parent_id) as upazila_code,m.geoid,m.field_name,m.geocode from m) select n.geoid,(select geocode from geo_data where id = n.field_parent_id) as district_code,n.upazila_code,n.geocode as union_code from n) select 'district' as list_name,field_name as label,geocode as name, null as district,null as upazilla,null as union_name,null as village from geo_data,g where field_type_id = 86 and geocode = g.district_code union all select 'upazila' as list_name,field_name as label,gd.geocode as name, (select geocode from geo_data where id = gd.field_parent_id) as district,null as upazilla,null as union_name,null as village from geo_data gd,g where field_type_id = 88 and geocode = upazila_code union all select 'union_name' as list_name,field_name as label,gd.geocode as name, SUBSTR(geocode, 1, 2) as district,(select geocode from geo_data where id = gd.field_parent_id) as upazilla,null as union_name,null as village from geo_data gd,g where field_type_id = 89 and geocode = union_code union all select 'village' as list_name,field_name as label,gd.geocode as name, SUBSTR(geocode, 1, 2) as district,SUBSTR(geocode, 1, 4) as upazilla,(select geocode from geo_data where id = gd.field_parent_id) as union_name,null as village from geo_data gd,g where field_type_id = 92 and field_parent_id = g.geoid union all select 'para' as list_name,field_name as label,gd.geocode as name, SUBSTR(geocode, 1, 2) as district,SUBSTR(geocode, 1, 4) as upazilla,SUBSTR(geocode, 1, 6) as union_name,(select geocode from geo_data where id = gd.field_parent_id) as village from geo_data gd,g where field_type_id = 143 and geocode LIKE g.union_code || '%') select distinct on (name) * from f"
    geolocation_data = __db_fetch_values(geolocation_query)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="itemsets.csv"'
    writer = csv.writer(response)
    writer.writerow(['list_name', 'label', 'name', 'district', 'upazila', 'union_name', 'village'])
    for data in geolocation_data:
        writer.writerow([data[0], data[1], data[2], data[3], data[4], data[5], data[6]])
    return response


def upload_monthly_target_plan(request):
    if request.method == 'POST' and request.FILES['target_file']:
        upload_month = request.POST.get('upload_month')

        activity_date = datetime.datetime.strptime(upload_month, "%B %Y")

        target_file = request.FILES['target_file']
        fs = FileSystemStorage(location='targetforms')
        filename = fs.save(target_file.name, target_file)
        uploaded_file_path = fs.path(filename)

        df = pd.read_excel(uploaded_file_path, 'MIS Target Form', index_col=None,
                           header=1, na_values=['NaN'],
                           parse_cols="D,J,K,L,M", skiprows=2)

        df.rename(columns={'Unnamed: 0': 'subindicator'}, inplace=True)
        df.rename(columns={'Married': 'male_boys_married'}, inplace=True)
        df.rename(columns={'Unmarried': 'male_boys_unmarried'}, inplace=True)
        df.rename(columns={'Married.1': 'female_girls_married'}, inplace=True)
        df.rename(columns={'Unmarried.1': 'female_girls_unmarried'}, inplace=True)
        df['activity_date'] = activity_date

        df.dropna(subset=['male_boys_married', 'male_boys_unmarried', 'female_girls_married', 'female_girls_unmarried'],
                  how='all', inplace=True)

        for index, row in df.iterrows():
            check_update_insert(row)

    return render(request, 'planmodule/upload_mon_target.html')


def check_update_insert(row):
    row.fillna(0, inplace=True)
    check_data = __db_fetch_single_value("select count(*) from plan_mis_monthly_target where subindicator = '" + str(
        row['subindicator']) + "' and activity_date = DATE('" + str(row['activity_date']) + "')")
    if check_data == 0:
        __db_commit_query_void(
            "INSERT INTO public.plan_mis_monthly_target (id, activity_date, subindicator, male_boys_unmarried, male_boys_married, female_girls_unmarried, female_girls_married) VALUES(nextval('plan_mis_monthly_target_id_seq'::regclass), DATE('" + str(
                row['activity_date']) + "'), '" + str(row['subindicator']) + "', " + str(
                row['male_boys_unmarried']) + ", " + str(row['male_boys_married']) + ", " + str(
                row['female_girls_unmarried']) + ", " + str(row['female_girls_married']) + ")")
    else:
        __db_commit_query_void("UPDATE public.plan_mis_monthly_target SET male_boys_unmarried=" + str(
            row['male_boys_unmarried']) + ", male_boys_married=" + str(
            row['male_boys_married']) + ", female_girls_unmarried=" + str(
            row['female_girls_unmarried']) + ", female_girls_married=" + str(
            row['female_girls_married']) + " where subindicator = '" + str(
            row['subindicator']) + "' and activity_date = DATE('" + str(row['activity_date']) + "')")


@csrf_exempt
def get_marriage_info_list(request):
    username = request.GET.get('username')
    marriage_info_query = "SELECT data_id, pngo,(select field_name from geo_data where geocode = district limit 1) as district, (select field_name from geo_data where geocode = upazila limit 1) as upazila, (select field_name from geo_data where geocode = union_name limit 1) as union_name, (select field_name from geo_data where geocode = village limit 1) as village, (select field_name from geo_data where geocode = para limit 1) as para, adolescent_name, birth_date, age, guardian_name, marriage_date, age_marriage_time, case is_child_marriage when '1' then 'Yes' when '2' then 'No' end as is_child_marriage, case religion when '1' then 'ইসলাম' when '2' then 'সনাতন' when '3' then 'খ্রিস্টান' when '4' then 'অন্যান্য' end as religion, case signed_marriage_registration when '1' then 'Yes' when '2' then 'No' end as signed_marriage_registration, case got_benefit_from_project when '1' then 'Yes' when '2' then 'No' end as got_benefit_from_project, case got_life_skill_session when '1' then 'Yes' when '2' then 'No' end as got_life_skill_session, case family_condition when '1' then 'হত-দরিদ্র' when '2' then 'দরিদ্র' when '3' then 'নিম্নবিত্ত' when '4' then 'নিম্নমধ্যবিত্ত' when '5' then 'মধ্যবিত্ত' when '6' then 'উচ্চ মধ্যবিত্ত' when '7' then 'উচ্চবিত্ত' end as family_condition, case hh_head_occupation WHEN '1' then 'কৃষিজীবি' WHEN '2' then 'মৎসজীবি' WHEN '3' then 'দিন মজুরী' WHEN '4' then 'ক্ষুদ্র ব্যবসা ' WHEN '5' then 'ব্যবসা' WHEN '6' then 'রিক্সা/ভ্যান চালক' WHEN '7' then 'চাকুরী' WHEN '8' then 'শিক্ষক' WHEN '9' then 'গৃহীণি' WHEN '99' then 'অন্যান্য' end as hh_head_occupation, education_qualification, case dropped_from_school when '1' then 'Yes' when '2' then 'No' end as dropped_from_school, school_name, case maritial_status when '1' then '১ম' when '2' then '২য়' when '3' then '৩য়' end as maritial_status, husband_info, husband_name, husband_birth_date, husband_age, case husband_occupation when '1' then 'কৃষিজীবি' when '2' then 'মৎসজীবি' when '3' then 'দিন মজুরী' when '4' then 'ক্ষুদ্র ব্যবসা ' when '5' then 'ব্যবসা' when '6' then 'রিক্সা/ভ্যান চালক' when '7' then 'চাকুরী' when '99' then 'অন্যান্য' end as husband_occupation, husband_edu_qualification, case husband_same_locality when '1' then 'Yes' when '2' then 'No' end as husband_same_locality, case child_marriage_cause when '1' then 'অর্থনৈতিক কারণ (খাওয়ার জন্য একটি মুখ কমেছে)' when '2' then 'নিরাপত্তাজনিত কারণ' when '3' then 'সাংস্কৃতিক কারণ (সামাজিক চর্চা)' when '4' then 'ভাল পাত্র' when '5' then 'মাসিক শুরু হয়েছে' when '6' then 'পারিবারিক সম্মান (কুৎসার ভয়ে, প্রেমে পড়া, রাজনৈতিক নেতার নজর)' when '7' then 'স্কুল ছেড়ে দিয়েছিল' when '8' then 'কিছু করছিলো না' when '99' then 'অন্যান্য' end as child_marriage_cause, date, username FROM public.vw_plan_marriage_info WHERE union_name :: text IN ( SELECT ( SELECT geocode FROM geo_data WHERE id = geoid) FROM usermodule_catchment_area WHERE user_id = ( SELECT id FROM auth_user WHERE username = '" + str(
        username) + "'))"
    marriage_info_data = __db_fetch_values_dict(marriage_info_query)
    return HttpResponse(json.dumps(marriage_info_data))


def quryExecution(query):
    cursor = connection.cursor()
    cursor.execute(query)
    value = cursor.fetchone()
    cursor.close()
    return value


def commnity_orientation_form(request):
    id_string = 'community_orientation'
    query = "SELECT id, uuid  FROM logger_xform where id_string = 'community_orientation'"
    queryResult = quryExecution(query)
    xform_id = queryResult[0]
    form_uuid = str(queryResult[1])
    username = request.user.username
    select_data = json.dumps(__db_fetch_values_dict(
        "select replace(field_name,'/','__') as field_name,value_text,value_label::json->>'bangla' as bn_label,value_label::json->>'English' as en_label from xform_extracted where xform_id = (select id from public.logger_xform where id_string = '" + str(
            id_string) + "') and field_type in ('select one','select all that apply') "))

    return render(request, "planmodule/commnity_orientation.html",
                  {'id_string': id_string, 'xform_id': xform_id,
                   'form_uuid': form_uuid, 'username': username, 'select_data': select_data,
                   })


def plan_mis_report(request):
    displayflag = 'none'
    from_date = '#######'
    if request.method == "POST":
        from_date = request.POST.get('from_date')
        report_date = datetime.datetime.strptime(from_date, '%B %Y')
        activity_month = report_date.strftime('%Y-%m') + '%'
        monthly_target_query = "select subindicator as subindicator_target,male_boys_married as male_boys_married_target,male_boys_unmarried as male_boys_unmarried_target,female_girls_married as female_girls_married_target,female_girls_unmarried as female_girls_unmarried_target,male_boys_married + male_boys_unmarried + female_girls_married + female_girls_unmarried as total from plan_mis_monthly_target where activity_date::text LIKE '" + str(
            activity_month) + "'"
        monthly_target_data = json.dumps(__db_fetch_values_dict(monthly_target_query))
        monthly_achievement_query = "with total as(select 'IR1_1A_011' as subindicator_ach, COUNT(id_adolescent) filter(where maritial_status::int = 1 and group_type::int = 1) as male_boys_married_ach, count(id_adolescent) filter (where maritial_status::int = 2 and group_type::int = 1) as male_boys_unmarried_ach, count(id_adolescent) filter (where maritial_status::int = 1 and group_type::int = 2) as female_girls_married_ach, count(id_adolescent) filter (where maritial_status::int = 2 and group_type::int = 2) as female_girls_unmarried_ach from vw_grp_all_sessions where session_date like '" + str(
            activity_month) + "' union all select 'IR3_3F_512' as subindicator_ach, sum(boy_10_14_married::int) as male_boys_married_ach, sum(boy_10_14_unmarried::int) as male_boys_unmarried_ach, sum(girl_10_14_married::int) as female_girls_married_ach, sum(girl_10_14_unmarried::int) as female_girls_unmarried_ach from vw_cf_miscellaneous_activity where activity_name = 'IR3_3F_51' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_3F_513' as subindicator_ach, sum(boy_15_19_married::int) as male_boys_married_ach, sum(boy_15_19_unmarried::int) as male_boys_unmarried_ach, sum(girl_15_19_married::int) as female_girls_married_ach, sum(girl_15_19_unmarried::int) as female_girls_unmarried_ach from vw_cf_miscellaneous_activity where activity_name = 'IR3_3F_51' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_4A_302' as subindicator_ach, sum(male_married::int) as male_boys_married_ach, sum(male_unmarried::int) as male_boys_unmarried_ach, sum(female_married::int) as female_girls_married_ach, sum(female_unmarried::int) as female_girls_unmarried_ach from vw_cf_miscellaneous_activity where activity_name = 'IR2_4A_30' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_3F_522' as subindicator_ach, sum(boy_15_19_married::int) as male_boys_married_ach, sum(boy_15_19_unmarried::int) as male_boys_unmarried_ach, sum(girl_15_19_married::int) as female_girls_married_ach, sum(girl_15_19_unmarried::int) as female_girls_unmarried_ach from vw_cf_miscellaneous_activity where activity_name = 'IR3_3F_52' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_3F_532' as subindicator_ach, sum(boy_15_19_married::int) as male_boys_married_ach, sum(boy_15_19_unmarried::int) as male_boys_unmarried_ach, sum(girl_15_19_married::int) as female_girls_married_ach, sum(girl_15_19_unmarried::int) as female_girls_unmarried_ach from vw_cf_miscellaneous_activity where activity_name = 'IR3_3F_53' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_3F_541' as subindicator_ach, sum(boy_10_14_married::int) as male_boys_married_ach, sum(boy_10_14_unmarried::int) as male_boys_unmarried_ach, sum(girl_10_14_married::int) as female_girls_married_ach, sum(girl_10_14_unmarried::int) as female_girls_unmarried_ach from vw_cf_miscellaneous_activity where activity_name = 'IR3_3F_54' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_3F_521' as subindicator_ach, sum(boy_10_14_married::int) as male_boys_married_ach, sum(boy_10_14_unmarried::int) as male_boys_unmarried_ach, sum(girl_10_14_married::int) as female_girls_married_ach, sum(girl_10_14_unmarried::int) as female_girls_unmarried_ach from vw_cf_miscellaneous_activity where activity_name = 'IR3_3F_52' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_3F_531' as subindicator_ach, sum(boy_10_14_married::int) as male_boys_married_ach, sum(boy_10_14_unmarried::int) as male_boys_unmarried_ach, sum(girl_10_14_married::int) as female_girls_married_ach, sum(girl_10_14_unmarried::int) as female_girls_unmarried_ach from vw_cf_miscellaneous_activity where activity_name = 'IR3_3F_53' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_3F_542' as subindicator_ach, sum(boy_15_19_married::int) as male_boys_married_ach, sum(boy_15_19_unmarried::int) as male_boys_unmarried_ach, sum(girl_15_19_married::int) as female_girls_married_ach, sum(girl_15_19_unmarried::int) as female_girls_unmarried_ach from vw_cf_miscellaneous_activity where activity_name = 'IR3_3F_54' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_2C_421' as subindicator_ach, sum(male_married::int) as male_boys_married_ach, sum(male_unmarried::int) as male_boys_unmarried_ach, sum(female_married::int) as female_girls_married_ach, sum(female_unmarried::int) as female_girls_unmarried_ach from vw_cf_miscellaneous_activity where activity_name = 'IR3_2C_42' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_1A_362' as subindicator_ach, COUNT(*) filter (where got_service::int = 1 AND age::int >= 15 AND age::int <= 19 AND maritial_status = 'Married' and sex_label = 'Male') as male_boys_married_ach, count(*) filter (where got_service::int = 1 AND age::int >= 15 AND age::int <= 19 AND maritial_status = 'Unmarried' and sex_label = 'Male') as male_boys_unmarried_ach, count(*) filter (where got_service::int = 1 AND age::int >= 15 AND age::int <= 19 AND maritial_status = 'Married' and sex_label = 'Female') as female_girls_married_ach, count(*) filter (where got_service::int = 1 AND age::int >= 15 AND age::int <= 19 AND maritial_status = 'Unarried' and sex_label = 'Female') as female_girls_unmarried_ach from vw_referral_followup where follow_up_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_012' as subindicator_ach, COUNT(id_adolescent) filter (where maritial_status::int = 1 and group_type::int = 3) as male_boys_married_ach, count(id_adolescent) filter (where maritial_status::int = 2 and group_type::int = 3) as male_boys_unmarried_ach, count(id_adolescent) filter (where maritial_status::int = 1 and group_type::int = 4) as female_girls_married_ach, count(id_adolescent) filter (where maritial_status::int = 2 and group_type::int = 4) as female_girls_unmarried_ach from vw_grp_all_sessions where session_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_021' as subindicator_ach, COUNT(*) filter (where maritial_status::int = 1 and group_type::int = 1 and session_count = 1) as male_boys_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 1 and session_count = 1) as male_boys_unmarried_ach, count(*) filter (where maritial_status::int = 1 and group_type::int = 2 and session_count = 1) as female_girls_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 2 and session_count = 1) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "' union all select 'IR3_1A_361' as subindicator_ach, COUNT(*) filter (where got_service::int = 1 AND age::int >= 10 AND age::int <= 14 AND maritial_status = 'Married' and sex_label = 'Male') as male_boys_married_ach, count(*) filter (where got_service::int = 1 AND age::int >= 10 AND age::int <= 14 AND maritial_status = 'Unmarried' and sex_label = 'Male') as male_boys_unmarried_ach, count(*) filter (where got_service::int = 1 AND age::int >= 10 AND age::int <= 14 AND maritial_status = 'Married' and sex_label = 'Female') as female_girls_married_ach, count(*) filter (where got_service::int = 1 AND age::int >= 10 AND age::int <= 14 AND maritial_status = 'Unarried' and sex_label = 'Female') as female_girls_unmarried_ach from vw_referral_followup where follow_up_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_022' as subindicator_ach, COUNT(*) filter (where maritial_status::int = 1 and group_type::int = 3 and session_count = 1) as male_boys_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 3 and session_count = 1) as male_boys_unmarried_ach, count(*) filter (where maritial_status::int = 1 and group_type::int = 4 and session_count = 1) as female_girls_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 4 and session_count = 1) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_031' as subindicator_ach, COUNT(*) filter (where maritial_status::int = 1 and group_type::int = 1 and session_count = 2) as male_boys_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 1 and session_count = 2) as male_boys_unmarried_ach, count(*) filter (where maritial_status::int = 1 and group_type::int = 2 and session_count = 2) as female_girls_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 2 and session_count = 2) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_032' as subindicator_ach, COUNT(*) filter (where maritial_status::int = 1 and group_type::int = 3 and session_count = 2) as male_boys_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 3 and session_count = 2) as male_boys_unmarried_ach, count(*) filter (where maritial_status::int = 1 and group_type::int = 4 and session_count = 2) as female_girls_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 4 and session_count = 2) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_041' as subindicator_ach, COUNT(*) filter (where maritial_status::int = 1 and group_type::int = 1 and session_count = 3) as male_boys_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 1 and session_count = 3) as male_boys_unmarried_ach, count(*) filter (where maritial_status::int = 1 and group_type::int = 2 and session_count = 3) as female_girls_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 2 and session_count = 3) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_042' as subindicator_ach, COUNT(*) filter (where maritial_status::int = 1 and group_type::int = 3 and session_count = 3) as male_boys_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 3 and session_count = 3) as male_boys_unmarried_ach, count(*) filter (where maritial_status::int = 1 and group_type::int = 4 and session_count = 3) as female_girls_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 4 and session_count = 3) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_051' as subindicator_ach, COUNT(*) filter (where maritial_status::int = 1 and group_type::int = 1 and session_count = 4) as male_boys_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 1 and session_count = 4) as male_boys_unmarried_ach, count(*) filter (where maritial_status::int = 1 and group_type::int = 2 and session_count = 4) as female_girls_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 2 and session_count = 4) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_052' as subindicator_ach, COUNT(*) filter (where maritial_status::int = 1 and group_type::int = 3 and session_count = 4) as male_boys_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 3 and session_count = 4) as male_boys_unmarried_ach, count(*) filter (where maritial_status::int = 1 and group_type::int = 4 and session_count = 4) as female_girls_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 4 and session_count = 4) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_061' as subindicator_ach, COUNT(*) filter (where maritial_status::int = 1 and group_type::int = 1 and session_count = 5) as male_boys_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 1 and session_count = 5) as male_boys_unmarried_ach, count(*) filter (where maritial_status::int = 1 and group_type::int = 2 and session_count = 5) as female_girls_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 2 and session_count = 5) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_062' as subindicator_ach, COUNT(*) filter (where maritial_status::int = 1 and group_type::int = 3 and session_count = 5) as male_boys_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 3 and session_count = 5) as male_boys_unmarried_ach, count(*) filter (where maritial_status::int = 1 and group_type::int = 4 and session_count = 5) as female_girls_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 4 and session_count = 5) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_071' as subindicator_ach, COUNT(*) filter (where maritial_status::int = 1 and group_type::int = 3 and session_count = 6) as male_boys_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 3 and session_count = 6) as male_boys_unmarried_ach, count(*) filter (where maritial_status::int = 1 and group_type::int = 4 and session_count = 6) as female_girls_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 4 and session_count = 6) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_081' as subindicator_ach, COUNT(*) filter (where maritial_status::int = 1 and group_type::int = 3 and session_count = 7) as male_boys_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 3 and session_count = 7) as male_boys_unmarried_ach, count(*) filter (where maritial_status::int = 1 and group_type::int = 4 and session_count = 7) as female_girls_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 4 and session_count = 7) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_091' as subindicator_ach, COUNT(*) filter (where maritial_status::int = 1 and group_type::int = 3 and session_count = 8) as male_boys_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 3 and session_count = 8) as male_boys_unmarried_ach, count(*) filter (where maritial_status::int = 1 and group_type::int = 4 and session_count = 8) as female_girls_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 4 and session_count = 8) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_101' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR1_1A_10' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR1_1A_121' as subindicator_ach, COUNT(*) filter (where maritial_status::int = 1 and group_type::int = 1 and session_count > 0 and ethnicity in (2,3,4,5)) as male_boys_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 1 and session_count > 0 and ethnicity in (2,3,4,5)) as male_boys_unmarried_ach, count(*) filter (where maritial_status::int = 1 and group_type::int = 2 and session_count > 0 and ethnicity in (2,3,4,5)) as female_girls_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 2 and session_count > 0 and ethnicity in (2,3,4,5)) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_122' as subindicator_ach, COUNT(*) filter (where maritial_status::int = 1 and group_type::int = 3 and session_count > 0 and ethnicity in (2,3,4,5)) as male_boys_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 3 and session_count > 0 and ethnicity in (2,3,4,5)) as male_boys_unmarried_ach, count(*) filter (where maritial_status::int = 1 and group_type::int = 4 and session_count > 0 and ethnicity in (2,3,4,5)) as female_girls_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 4 and session_count > 0 and ethnicity in (2,3,4,5)) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_131' as subindicator_ach, COUNT(*) filter (where maritial_status::int = 1 and group_type::int = 1 and session_count = 5 and ethnicity in (2,3,4,5)) as male_boys_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 1 and session_count = 5 and ethnicity in (2,3,4,5)) as male_boys_unmarried_ach, count(*) filter (where maritial_status::int = 1 and group_type::int = 2 and session_count = 5 and ethnicity in (2,3,4,5)) as female_girls_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 2 and session_count = 5 and ethnicity in (2,3,4,5)) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_132' as subindicator_ach, COUNT(*) filter (where maritial_status::int = 1 and group_type::int = 3 and session_count = 8 and ethnicity in (2,3,4,5)) as male_boys_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 3 and session_count = 8 and ethnicity in (2,3,4,5)) as male_boys_unmarried_ach, count(*) filter (where maritial_status::int = 1 and group_type::int = 4 and session_count = 8 and ethnicity in (2,3,4,5)) as female_girls_married_ach, count(*) filter (where maritial_status::int = 2 and group_type::int = 4 and session_count = 8 and ethnicity in (2,3,4,5)) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "' union all select 'B_B3_572' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'B_B3_57' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR1_4A_202' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR1_4A_20' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_1A_212' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR2_1A_212' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_1A_213' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR2_1A_213' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_1A_222' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR2_1A_22' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_2B_232' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR2_2B_23' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_2B_242' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR2_2B_24' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_3C_282' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR2_3C_28' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_3C_291' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR2_3C_29' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_4C_331' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR2_4C_32' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_1A_341' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR3_1A_34' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_2A_371' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR3_2A_37' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_2A_391' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR3_2A_38' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_2B_401' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR3_2B_40' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_2B_411' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR3_2B_41' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_3A_431' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR3_3A_43' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_3A_441' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR3_3A_44' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_3B_451' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR3_3B_45' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_3B_461' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR3_3B_46' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_3C_471' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR3_3C_471' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_3B_262' as subindicator_ach, sum(male_married::int) as male_boys_married_ach, sum(male_unmarried::int) as male_boys_unmarried_ach, sum(female_married::int) as female_girls_married_ach, sum(female_unmarried::int) as female_girls_unmarried_ach from vw_cf_miscellaneous_activity where activity_name = 'IR2_3B_26' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_3B_271' as subindicator_ach, sum(male_married::int) as male_boys_married_ach, sum(male_unmarried::int) as male_boys_unmarried_ach, sum(female_married::int) as female_girls_married_ach, sum(female_unmarried::int) as female_girls_unmarried_ach from vw_cf_miscellaneous_activity where activity_name = 'IR2_3B_27' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_3C_472' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR3_3C_472' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_3E_491' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR3_3E_491' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_3E_492' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR3_3E_492' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_3E_493' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR3_3E_493' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_3F_501' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR3_3F_50' and activity_date::text like '" + str(
            activity_month) + "' union all select 'B_B1_552' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'B_B1_55' and activity_date::text like '" + str(
            activity_month) + "' union all select 'B_B2_562' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'B_B2_56' and activity_date::text like '" + str(
            activity_month) + "' union all select 'B_B4_582' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'B_B4_58' and activity_date::text like '" + str(
            activity_month) + "' union all select 'C_C1_601' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'B_C1_60' and activity_date::text like '" + str(
            activity_month) + "' union all select 'C_C2_611' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'B_C2_61' and activity_date::text like '" + str(
            activity_month) + "' union all select 'C_C3_621' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'B_C3_62' and activity_date::text like '" + str(
            activity_month) + "' union all select 'C_C4_631' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'B_C4_63' and activity_date::text like '" + str(
            activity_month) + "' union all select 'B_B5_592' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'B_B5_59' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_2A_232' as subindicator_ach, sum(male_boys_married) as male_boys_married_ach, sum(male_boys_unmarried) as male_boys_unmarried_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = 'IR2_2A_23' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_1A_351' as subindicator_ach, COUNT(*) filter(where referral_cause::int >= 1 and referral_cause::int <=19 and age::int >=10 and age::int <= 14 and maritial_status::int = 1 and gender::int = 1) as male_boys_married_ach, COUNT(*) filter (where referral_cause::int >= 1 and referral_cause::int <=19 and age::int >=10 and age::int <= 14 and maritial_status::int = 3 and gender::int = 1) as male_boys_unmarried_ach, COUNT(*) filter (where referral_cause::int >= 1 and referral_cause::int <=19 and age::int >=10 and age::int <= 14 and maritial_status::int = 1 and gender::int = 2) as female_girls_married_ach, COUNT(*) filter (where referral_cause::int >= 1 and referral_cause::int <=19 and age::int >=10 and age::int <= 14 and maritial_status::int = 3 and gender::int = 2) as female_girls_unmarried_ach from vw_referral_reg_unnest where refferal_date::text like '" + str(
            activity_month) + "' union all select 'IR3_1A_352' as subindicator_ach, COUNT(*) filter (where referral_cause::int >= 1 and referral_cause::int <=19 and age::int >=15 and age::int <= 19 and maritial_status::int = 1 and gender::int = 1) as male_boys_married_ach, COUNT(*) filter (where referral_cause::int >= 1 and referral_cause::int <=19 and age::int >=15 and age::int <= 19 and maritial_status::int = 3 and gender::int = 1) as male_boys_unmarried_ach, COUNT(*) filter (where referral_cause::int >= 1 and referral_cause::int <=19 and age::int >=15 and age::int <= 19 and maritial_status::int = 1 and gender::int = 2) as female_girls_married_ach, COUNT(*) filter (where referral_cause::int >= 1 and referral_cause::int <=19 and age::int >=15 and age::int <= 19 and maritial_status::int = 3 and gender::int = 2) as female_girls_unmarried_ach from vw_referral_reg_unnest where refferal_date::text like '" + str(
            activity_month) + "' union all select 'IR1_1A_111' as subindicator_ach, sum(session_count) filter(where maritial_status::int = 1 and group_type::int = 1) as male_boys_married_ach, sum(session_count) filter (where maritial_status::int = 2 and group_type::int = 1) as male_boys_unmarried_ach, sum(session_count) filter (where maritial_status::int = 1 and group_type::int = 2) as female_girls_married_ach, sum(session_count) filter (where maritial_status::int = 2 and group_type::int = 2) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "' union all select 'IR1_1A_112' as subindicator_ach, sum(session_count) filter (where maritial_status::int = 1 and group_type::int = 3) as male_boys_married_ach, sum(session_count) filter (where maritial_status::int = 2 and group_type::int = 3) as male_boys_unmarried_ach, sum(session_count) filter (where maritial_status::int = 1 and group_type::int = 4) as female_girls_married_ach, sum(session_count) filter (where maritial_status::int = 2 and group_type::int = 4) as female_girls_unmarried_ach from vw_grp_adol_session_counter where session_date like '" + str(
            activity_month) + "') select subindicator_ach,COALESCE(male_boys_married_ach,0) male_boys_married_ach,COALESCE(male_boys_unmarried_ach,0) male_boys_unmarried_ach,COALESCE(female_girls_married_ach,0) female_girls_married_ach,COALESCE(female_girls_unmarried_ach,0) female_girls_unmarried_ach, COALESCE(female_girls_unmarried_ach,0) + COALESCE(male_boys_unmarried_ach,0) + COALESCE(female_girls_married_ach,0) + COALESCE(male_boys_married_ach,0) as total_ach from total"
        monthly_achievement_data = json.dumps(__db_fetch_values_dict(monthly_achievement_query))
        sc_ma_query = "with t as(select 'IR1_2A_141' as subindicator_ach, count(*) as total_ach from vw_comm_orientation where orientation_type::int = 1 and community_representative_type::int = 1 and date like '" + str(
            activity_month) + "' union all select 'IR3_3D_481' as subindicator_ach,sum(ir3_3d_48::int) as total_ach from vw_cf_miscellaneous_activity where activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_3D_482' as subindicator_ach, sum(no_of_activity::int) as total_ach from vw_cf_miscellaneous_activity where activity_name = 'IR3_3D_48' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_4A_301' as subindicator_ach, sum(no_of_activity::int) as total_ach from vw_cf_miscellaneous_activity where activity_name = 'IR2_4A_30' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR1_2A_142' as subindicator_ach, count(*) as total_ach from vw_comm_orientation where orientation_type::int = 1 and community_representative_type::int = 2 and date like '" + str(
            activity_month) + "' union all select 'IR1_2A_143' as subindicator_ach, count(*) as total_ach from vw_comm_orientation where orientation_type::int = 1 and community_representative_type::int = 3 and date like '" + str(
            activity_month) + "' union all select 'IR1_2A_144' as subindicator_ach, count(*) as total_ach from vw_comm_orientation where orientation_type::int = 1 and community_representative_type::int in(4,5) and date like '" + str(
            activity_month) + "' union all select 'IR1_2A_151' as subindicator_ach, count(*) as total_ach from vw_comm_orientation where promised::int = 1 and issue_based_meeting_present_type::int =2 and date like '" + str(
            activity_month) + "' union all select 'IR1_2A_152' as subindicator_ach, count(*) as total_ach from vw_comm_orientation where promised::int = 1 and issue_based_meeting_present_type::int =1 and date like '" + str(
            activity_month) + "' union all select 'IR1_3A_181' as subindicator_ach, count(*) as total_ach from vw_comm_orientation where orientation_type::int = 4 and date like '" + str(
            activity_month) + "' union all select 'IR1_3A_182' as subindicator_ach, count(*) as total_ach from vw_comm_orientation where issue_based_meeting_present_type::int = 2 and date like '" + str(
            activity_month) + "' union all select 'IR1_3A_183' as subindicator_ach, count(*) as total_ach from vw_comm_orientation where issue_based_meeting_present_type::int = 1 and date like '" + str(
            activity_month) + "' union all select 'IR2_3A_251' as subindicator_ach, count(*) as total_ach from vw_comm_orientation where married_adolescent_or_couple_type::int = 1 and date like '" + str(
            activity_month) + "' union all select 'IR2_4B_311' as subindicator_ach, count(*) as total_ach from vw_comm_orientation where orientation_type::int = 3 and date like '" + str(
            activity_month) + "' union all select 'IR2_4B_312' as subindicator_ach, count(*) as total_ach from vw_comm_orientation where orientation_type::int = 3 and married_adolescent_or_couple_type::int = 1 and date like '" + str(
            activity_month) + "' union all select 'IR1_2A_161' as subindicator_ach, count(*) as total_ach from vw_plan_marriage_info where date like '" + str(
            activity_month) + "' union all select 'IR1_2A_171' as subindicator_ach, count(*) as total_ach from vw_cmp_registration where sex::int = 2 and date_child_marriage_prevented like '" + str(
            activity_month) + "' union all select 'IR1_4A_201' as subindicator_ach, sum(number_of_activity) as total_ach from plan_mis_report_district_form where activity_id = 'IR1_4A_20' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_1A_211' as subindicator_ach, sum(number_of_activity) as total_ach from plan_mis_report_district_form where activity_id = 'IR2_1A_212' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_1A_221' as subindicator_ach, sum(number_of_activity) as total_ach from plan_mis_report_district_form where activity_id = 'IR2_1A_21' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_2A_231' as subindicator_ach, sum(number_of_activity) as total_ach from plan_mis_report_district_form where activity_id = 'IR2_2A_23' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_2B_241' as subindicator_ach, sum(number_of_activity) as total_ach from plan_mis_report_district_form where activity_id = 'IR2_2B_24' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_3C_281' as subindicator_ach, sum(number_of_activity) as total_ach from plan_mis_report_district_form where activity_id = 'IR2_3C_28' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_4C_321' as subindicator_ach, sum(number_of_activity) as total_ach from plan_mis_report_district_form where activity_id = 'IR2_4C_32' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR3_2A_381' as subindicator_ach, sum(number_of_activity) as total_ach from plan_mis_report_district_form where activity_id = 'IR3_2A_38' and activity_date::text like '" + str(
            activity_month) + "' union all select 'B_B1_551' as subindicator_ach, sum(number_of_activity) as total_ach from plan_mis_report_district_form where activity_id = 'B_B1_55' and activity_date::text like '" + str(
            activity_month) + "' union all select 'B_B2_561' as subindicator_ach, sum(number_of_activity) as total_ach from plan_mis_report_district_form where activity_id = 'B_B2_56' and activity_date::text like '" + str(
            activity_month) + "' union all select 'B_B3_571' as subindicator_ach, sum(number_of_activity) as total_ach from plan_mis_report_district_form where activity_id = 'B_B3_57' and activity_date::text like '" + str(
            activity_month) + "' union all select 'B_B4_581' as subindicator_ach, sum(number_of_activity) as total_ach from plan_mis_report_district_form where activity_id = 'B_B4_58' and activity_date::text like '" + str(
            activity_month) + "' union all select 'B_B5_591' as subindicator_ach, sum(number_of_activity) as total_ach from plan_mis_report_district_form where activity_id = 'B_B5_59' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR2_3B_261' as subindicator_ach, sum(no_of_activity::int) as total_ach from vw_cf_miscellaneous_activity where activity_name = 'IR2_3B_26' and activity_date::text like '" + str(
            activity_month) + "' union all select 'IR1_4A_191' as subindicator_ach,sum(number_of_activity) as total_ach from plan_mis_report_district_form where activity_id = 'IR1_4A_191' and activity_date::text like '" + str(
            activity_month) + "') select subindicator_ach,COALESCE(total_ach,0) total_ach from t"
        sc_ma_data = json.dumps(__db_fetch_values_dict(sc_ma_query))

        dc_ma_query = "with t as( select '1641' as subindicator_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = '164' and activity_date::text like '" + str(
            activity_month) + "' union all select '2651' as subindicator_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = '265' and activity_date::text like '" + str(
            activity_month) + "' union all select '3661' as subindicator_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = '366' and activity_date::text like '" + str(
            activity_month) + "' union all select '4672' as subindicator_ach, sum(female_girls_married) as female_girls_married_ach, sum(female_girls_unmarried) as female_girls_unmarried_ach from plan_mis_report_district_form where activity_id = '467' and activity_date::text like '" + str(
            activity_month) + "') select subindicator_ach,COALESCE(female_girls_married_ach, 0) female_girls_married_ach,COALESCE(female_girls_unmarried_ach,0) female_girls_unmarried_ach,COALESCE(female_girls_married_ach, 0)+COALESCE(female_girls_unmarried_ach,0) as total_ach from t"
        dc_ma_data = json.dumps(__db_fetch_values_dict(dc_ma_query))
        displayflag = 'block'
    else:
        monthly_target_data = {}
        monthly_achievement_data = {}
        sc_ma_data = {}
        dc_ma_data = {}
    return render(request, "planmodule/plan_mis_report.html",
                  {'from_date': from_date, 'monthly_target_data': monthly_target_data,
                   'monthly_achievement_data': monthly_achievement_data,
                   'sc_ma_data': sc_ma_data, 'dc_ma_data': dc_ma_data, 'displayflag': displayflag})


@csrf_exempt
def get_upazilas(request):
    upazila_data = []
    reqBody = json.loads(request.body)
    district = reqBody.get('serach_key')
    if district is not None:
        query = "select geoid from usermodule_catchment_area where user_id = " + str(request.user.id)
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        if not df.empty and df.geoid.tolist()[0] != 9377:
            geoid = df.geoid.tolist()[0]
            upazila_query = "select id, field_name as name , geocode as  value  from geo_data where field_type_id = 88 and field_parent_id =  any(  select id from geo_data where geocode = '" + str(
                district) + "') and id =" + str(geoid)
        else:
            upazila_query = "select id, field_name as name, geocode as value  from geo_data where field_type_id = 88 and field_parent_id =  any(  select id from geo_data where geocode = '" + str(
                district) + "')"
        upazila_data = json.dumps(__db_fetch_values_dict(upazila_query))
    return HttpResponse(upazila_data)


@csrf_exempt
def get_unions(request):
    union_data = []
    reqBody = json.loads(request.body)
    upazila = reqBody.get('serach_key')
    if upazila is not None:
        union_query = "select id,field_name as name, geocode as value from geo_data where field_type_id = 89 and field_parent_id =  any(  select id from geo_data where geocode = '" + str(
            upazila) + "')"
        union_data = json.dumps(__db_fetch_values_dict(union_query))
    return HttpResponse(union_data)

@csrf_exempt
def get_villages(request):
    villages_data = []
    reqBody = json.loads(request.body)
    union = reqBody.get('serach_key')
    if union is not None:
        village_query = "select id,field_name as name, geocode as value from geo_data where field_type_id = 92 and field_parent_id =  any(  select id from geo_data where geocode = '" + str(
            union) + "')"
        print(village_query)
        villages_data = json.dumps(__db_fetch_values_dict(village_query))
    return HttpResponse(villages_data)


@csrf_exempt
def get_paras(request):
    para_data = []
    reqBody = json.loads(request.body)
    village = reqBody.get('serach_key')
    if village is not None:
        village_query = "select id,field_name as name, geocode as value from geo_data where field_type_id = 143 and field_parent_id =  any(  select id from geo_data where geocode = '" + str(
            village) + "')"

        para_data = json.dumps(__db_fetch_values_dict(village_query))
    return HttpResponse(para_data)


@csrf_exempt
def submitXMLData(request):
    jsondata = json.loads(request.body)
    xml_data = jsondata.get("xml_submission_file")
    tree = ET.XML(xml_data)

    file_path = "onadata/media/" + request.user.username + "/xml/"
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open("onadata/media/" + request.user.username + "/xml/submit_data.xml", "w+") as f:
        f.write(ET.tostring(tree))

    files = {'xml_submission_file': open(str(f.name), 'rb')}
    requests.post('http://' + request.META.get('HTTP_HOST') + '/' + request.user.username + '/submission', files=files)
    messages.success(request, '<i class="fa fa-check-circle"></i> Action Completed   successfully!',
                     extra_tags='alert-success crop-both-side')
    return HttpResponse("success!")


@csrf_exempt
def get_referrals_list(request):
    username = request.GET.get('username')
    # referral_list_query = "with m as(with t as(select value_text,value_label from xform_extracted where xform_id = 534 and field_name = 'referral_cause'), q as(select value_text,value_label from xform_extracted where xform_id = 534 and field_name = 'referral_place'), s as(select data_id as referral_id, pngo, district, upazila, union_name, village, para, hh_no, hh_head, adolescent_name, id_adolescent, age, gender, maritial_status, refferal_date, referral_place, referral_place_others, unnest(string_to_array(referral_cause,' ')) as referral_cause, referral_cause_other, refferer_name, username from vw_plan_referral_reg WHERE union_name :: text IN ( SELECT ( SELECT geocode FROM geo_data WHERE id = geoid) FROM usermodule_catchment_area WHERE user_id = ( SELECT id FROM auth_user WHERE username = '"+str(username)+"'))) select referral_id, pngo, district, upazila, union_name, village, para, hh_no, hh_head, adolescent_name, id_adolescent, age, case gender when '1' then 'Male' when '2' then 'Female' end as gender, case maritial_status when '1' then 'Unmarried' when '2' then 'Married' when '3' then 'Newly Married' end as maritial_status, refferal_date, q.value_label as referral_place, referral_place_others,t.value_label as referral_cause, referral_cause_other, refferer_name, username from t,s,q where t.value_text = s.referral_cause and q.value_text = s.referral_place) select referral_id, pngo, district, upazila, union_name, village, para, hh_no, hh_head, adolescent_name, id_adolescent, age, gender, maritial_status, refferal_date, referral_place, referral_place_others,string_agg(referral_cause,', ') as referral_cause, referral_cause_other, refferer_name, username from m group by referral_id, pngo, district, upazila, union_name, village, para, hh_no, hh_head, adolescent_name, id_adolescent, age, gender, maritial_status, refferal_date, referral_place, referral_place_others,referral_cause_other, refferer_name, username order by referral_id DESC"
    referral_list_query = "with m as(with t as(select value_text,value_label from xform_extracted where xform_id = 534 and field_name = 'referral_cause'), q as(select value_text,value_label from xform_extracted where xform_id = 534 and field_name = 'referral_place'), s as(select data_id as referral_id, pngo, district, upazila, union_name, village, para, hh_no, hh_head, adolescent_name, id_adolescent, age, gender, maritial_status, refferal_date, referral_place, referral_place_others, unnest(string_to_array(referral_cause,' ')) as referral_cause, referral_cause_other, refferer_name, username from vw_plan_referral_reg WHERE union_name :: text IN ( SELECT ( SELECT geocode FROM geo_data WHERE id = geoid) FROM usermodule_catchment_area WHERE user_id = ( SELECT id FROM auth_user WHERE username = '" + str(
        username) + "'))) select referral_id, pngo, district, upazila, union_name, village, para, hh_no, hh_head, adolescent_name, id_adolescent, age, case gender when '1' then 'Male' when '2' then 'Female' end as gender, case maritial_status when '1' then 'Unmarried' when '2' then 'Married' when '3' then 'Newly Married' end as maritial_status, refferal_date, q.value_label as referral_place, referral_place_others,t.value_label as referral_cause, referral_cause_other, refferer_name, username from t,s,q where t.value_text = s.referral_cause and q.value_text = s.referral_place) select referral_id, pngo, district, upazila, union_name, village, para, hh_no, hh_head, adolescent_name, id_adolescent, age, gender, maritial_status, refferal_date, referral_place, referral_place_others,string_agg(referral_cause,', ') as referral_cause, referral_cause_other, refferer_name, username from m where referral_id::text not in (select id_followup from public.vw_referral_followup) group by referral_id, pngo, district, upazila, union_name, village, para, hh_no, hh_head, adolescent_name, id_adolescent, age, gender, maritial_status, refferal_date, referral_place, referral_place_others,referral_cause_other, refferer_name, username order by referral_id DESC"
    referral_list_data = __db_fetch_values_dict(referral_list_query)
    return HttpResponse(json.dumps(referral_list_data))


@csrf_exempt
def get_facility_by_upazila(request):
    upazila = request.POST.get('upz')
    facility_list_data = __db_fetch_values_dict(
        "select facilty_id,facilty_name from plan_facilities where upazilla = " + str(upazila))
    return HttpResponse(json.dumps(facility_list_data))


@csrf_exempt
def get_session_list_by_group_type(request):
    group_type = request.GET.get('group_type')
    session_list = __db_fetch_values_dict(
        "with t as(select json_array_elements(json::json->'choices'->'session') as sessions_list from logger_xform where id = 558) select sessions_list->>'name' as session_no,sessions_list->'label' as session_name from t where sessions_list->>'myfilter' = '" + str(
            group_type) + "'")
    return HttpResponse(json.dumps(session_list))
