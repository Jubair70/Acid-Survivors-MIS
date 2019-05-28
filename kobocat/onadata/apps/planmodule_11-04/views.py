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
    query = "select id,DATE(registration_date) registration_date, (select field_name from geo_data where id = district) district,(select field_name from geo_data where id = upazilla) upazilla, facilty_name, facilty_id,Case when facility_type = 1 then 'FWCC' else 'CC' end facility_type from plan_facilities where pngo_id in " + str(
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
    return render(request, 'planmodule/add_facility_form.html',
                  {'district': district, 'org_id': org_id, 'org_name': org_name})


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
    data['facility_type'] = df.facility_type.tolist()[0]
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
                   'upazila': upazila, 'org_id': org_id, 'org_name': org_name})


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
    return HttpResponseRedirect("/planmodule/facility_list/")


@login_required
def delete_facility_form(request, facility_id):
    delete_query = "delete from plan_facilities where id = " + str(facility_id) + ""
    __db_commit_query(delete_query)
    return HttpResponseRedirect("/planmodule/facility_list/")


def getUpazilas(request):
    district = request.POST.get('dist')
    upazila_query = "select id,field_name from geo_data where field_type_id = 88 and field_parent_id = " + str(district)
    upazila_data = json.dumps(__db_fetch_values_dict(upazila_query))
    return HttpResponse(upazila_data)


def getUnions(request):
    upazila = request.POST.get('upz')
    union_query = "select geocode as id,field_name from geo_data where field_type_id = 89 and field_parent_id = (select id from geo_data where geocode = '"+str(upazila)+"')"
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
    query = "select id,(select field_name from public.geo_data where id = district) district,(select field_name from public.geo_data where id = upazilla) upazilla,DATE(execution_date) execution_date,(select facilty_name from public.plan_facilities where facilty_id::int = facility_id) facility_name,case when facility_type = 1 then 'FWCC' else 'CC' end facility_type,average_score_adolescents,average_score_service_providers,major_comments_adolescents,major_comments_service_providers from public.plan_scorecard where pngo_id in " + str(
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
        print
        pngo_id
        insert_query = "INSERT INTO public.plan_scorecard ( district, upazilla, pngo_id, execution_date, facility_id, facility_type, average_score_adolescents, average_score_service_providers, major_comments_adolescents, major_comments_service_providers, created_by, updated_by, created_at, updated_at) VALUES(" + str(
            district) + ", " + str(upazilla) + ", " + str(pngo_id) + ", '" + str(execution_date) + "', " + str(facility_id) + ", " + str(facility_type) + ", " + str(
            average_score_adolescents) + ", " + str(average_score_service_providers) + ", '" + str(
            major_comments_adolescents) + "', '" + str(major_comments_service_providers) + "', " + str(
            created_by) + ", " + str(updated_by) + ",now(),now())"
        print(insert_query)
        __db_commit_query(insert_query)
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
    return HttpResponseRedirect("/planmodule/scorecard_list/")



@login_required
def delete_scorecard_form(request, scorecard_id):
    delete_query = "delete from plan_scorecard where id = " + str(scorecard_id) + ""
    __db_commit_query(delete_query)
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
        query = "select id,(select field_name from public.geo_data where id = district) district,(select field_name from public.geo_data where id = upazilla) upazilla,DATE(execution_date) execution_date,(select facilty_name from public.plan_facilities where facilty_id::int = facility_id) facility_name,case when facility_type = 1 then 'FWCC' else 'CC' end facility_type,average_score_adolescents,average_score_service_providers,major_comments_adolescents,major_comments_service_providers from public.plan_scorecard where pngo_id in " + str(
            org)
        scorecard_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
        query = "select id,field_name from geo_data where field_type_id = 88 "
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        upz_id = df.id.tolist()
        upz_name = df.field_name.tolist()
        upazila = zip(upz_id, upz_name)
    else:
        upazila_geoid = df.geoid.tolist()[0]
        query = "select id,(select field_name from public.geo_data where id = district) district,(select field_name from public.geo_data where id = upazilla) upazilla,DATE(execution_date) execution_date,(select facilty_name from public.plan_facilities where facilty_id::int = facility_id) facility_name,case when facility_type = 1 then 'FWCC' else 'CC' end facility_type,average_score_adolescents,average_score_service_providers,major_comments_adolescents,major_comments_service_providers from public.plan_scorecard where upazilla = "+str(upazila_geoid)+" and  pngo_id in " + str(
            org)
        scorecard_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
        print(query)
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
        query = "select geoid from usermodule_catchment_area where user_id = "+str(request.user.id)
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        if not df.empty:
            upazila_geoid = df.geoid.tolist()[0]
            filter_query += " and upazilla = " + str(upazila_geoid)
    if pngo !="":
        filter_query += " and pngo_id = "+str(pngo)
    else:
        filter_query += " and pngo_id in " + str(org)
    query = "select id,(select field_name from public.geo_data where id = district) district,(select field_name from public.geo_data where id = upazilla) upazilla,DATE(execution_date) execution_date,(select facilty_name from public.plan_facilities where facilty_id::int = facility_id) facility_name,case when facility_type = 1 then 'FWCC' else 'CC' end facility_type,average_score_adolescents,average_score_service_providers,major_comments_adolescents,major_comments_service_providers from public.plan_scorecard "+str(filter_query)
    print(query)
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
    org = str(map(str, org_id_list))
    org = org.replace('[', '(').replace(']', ')')
    query = "with csa_reg as( select json->>'info/id_adolescent'id_adolescent,json->>'info/adolescent_name' adolescent_name,json->>'info/upazila' upazilla_id,json->>'info/union_name' union_id,json->>'business_start_month' business_start_month,(select id from public.usermodule_organizations where organization=(json->>'info/pngo'))pngo_id,json->>'info/pngo' pngo_name from public.logger_instance where xform_id = 555 and deleted_at is null) ,csa_reg_follow as ( select json->>'info/id_adolescent'id_adolescent,json->>'month' current_month,json->>'commodity_price' commodity_price,json->>'commodity_amount' commodity_amount,json->>'profit' profit,json->>'remarks' remarks from public.logger_instance where xform_id = 554 and deleted_at is null ) select csa_reg.*,current_month,commodity_price,commodity_amount,remarks,profit from csa_reg,csa_reg_follow where csa_reg.id_adolescent = csa_reg_follow.id_adolescent and pngo_id in " + str(org)
    csa_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)

    query_pngo = "select id,organization from public.usermodule_organizations where id in "+str(org)
    df = pandas.DataFrame()
    df = pandas.read_sql(query_pngo,connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id,org_name)

    query = "select geocode,field_name from geo_data where field_type_id = 88 "
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    upz_id = df.geocode.tolist()
    upz_name = df.field_name.tolist()
    upazila = zip(upz_id, upz_name)

    query = "select geocode,field_name from geo_data where field_type_id = 89"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    union_id = df.geocode.tolist()
    union_name = df.field_name.tolist()
    union = zip(union_id, union_name)

    return render(request, 'planmodule/csa_report.html', {
        'csa_list': csa_list,'organization':organization,'upazila':upazila,'union':union
    })


@login_required
def getCSAData(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    upazila = request.POST.get('upazila')
    union = request.POST.get('union')
    pngo = request.POST.get('pngo')

    filter_query = "and  current_month between '" + str(from_date) + "' and '" + str(to_date) + "'"
    if upazila !="":
        filter_query += " and upazilla_id::int = "+str(upazila)
    if pngo !="":
        filter_query += " and pngo_id::int = "+str(pngo)
    if union!="":
        filter_query += " and union_id::int = " + str(union)
    query = "with csa_reg as( select json->>'info/id_adolescent'id_adolescent,json->>'info/adolescent_name' adolescent_name,json->>'info/upazila' upazilla_id,json->>'info/union_name' union_id,json->>'business_start_month' business_start_month,(select id from public.usermodule_organizations where organization=(json->>'info/pngo'))pngo_id,json->>'info/pngo' pngo_name from public.logger_instance where xform_id = 555 and deleted_at is null) ,csa_reg_follow as ( select json->>'info/id_adolescent'id_adolescent,json->>'month' current_month,json->>'commodity_price' commodity_price,json->>'commodity_amount' commodity_amount,json->>'profit' profit,json->>'remarks' remarks from public.logger_instance where xform_id = 554 and deleted_at is null ) select csa_reg.*,current_month,commodity_price,commodity_amount,profit,remarks from csa_reg,csa_reg_follow where csa_reg.id_adolescent = csa_reg_follow.id_adolescent "+str(filter_query)
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
    query = "with t as( SELECT username, village_geocode, village_name, union_geocode, union_name, upazilla_geocode, upazilla_name, district_geocode, district_name, group_type, maritial_status, submission_date, test_type, group_id, adolescent_name, id_adolescent, number_obtained,case when number_obtained::int <=5 then 1 else 0 end poor,case when number_obtained::int >=6 and number_obtained::int <=9 then 1 else 0 end good,case when number_obtained::int >=10 then 1 else 0 end excellent FROM public.vw_life_skill_education_test where pngo_id in "+str(org)+")select group_id,case when test_type='1' then 'Pre' else 'Post' end test_type,submission_date,count(adolescent_name) enrolled,sum(poor) poor,sum(good) good,sum(excellent) excellent from t group by submission_date,poor,test_type,group_id"
    test_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)


    query_pngo = "select id,organization from public.usermodule_organizations where id in "+str(org)
    df = pandas.DataFrame()
    df = pandas.read_sql(query_pngo,connection)
    org_id = df.id.tolist()
    org_name = df.organization.tolist()
    organization = zip(org_id,org_name)

    query = "select geocode,field_name from geo_data where field_type_id = 88"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    upz_id = df.geocode.tolist()
    upz_name = df.field_name.tolist()
    upazila = zip(upz_id, upz_name)

    query = "select geocode,field_name from geo_data where field_type_id = 89"
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

    query_for_chart = "with t as( SELECT username, village_geocode, village_name, union_geocode, union_name, upazilla_geocode, upazilla_name, district_geocode, district_name, group_type, maritial_status, submission_date, test_type, group_id, adolescent_name, id_adolescent, number_obtained,case when number_obtained::int <=5 then 1 else 0 end poor,case when number_obtained::int >=6 and number_obtained::int <=9 then 1 else 0 end good,case when number_obtained::int >=10 then 1 else 0 end excellent FROM public.vw_life_skill_education_test)select test_type,sum(poor) poor,sum(good) good,sum(excellent) excellent from t group by test_type order by test_type"
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
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    upazila = request.POST.get('upazila')
    union = request.POST.get('union')
    pngo = request.POST.get('pngo')
    username = request.POST.get('username')
    group = request.POST.get('group')
    test_type = request.POST.get('test_type')
    marital_status = request.POST.get('marital_status')
    session = request.POST.get('session')

    filter_query = "where  submission_date between '" + str(from_date) + "' and '" + str(to_date) + "'"
    if len(group)!=0:
        if len(group) == 1:
            filter_query += " and group_type::int = " + str(group)
        elif len(group) == 2:
            group = "("+group[0]+","+group[1]+")"
            filter_query += " and group_type::int in " + str(group)

    if upazila !="":
        filter_query += " and upazilla_geocode::int = "+str(upazila)
    if pngo !="":
        filter_query += " and username in (select username from auth_user where id in(select user_id from usermodule_usermoduleprofile where organisation_name_id = "+str(pngo)+"))"
    if union!="":
        filter_query += " and union_geocode::int = " + str(union)
    if username!="":
        filter_query += " and username = (select username from auth_user where id ="+ str(username)+")"

    if test_type!="":
        filter_query += " and test_type::int = " + str(test_type)
    if marital_status!="":
        filter_query += " and maritial_status::int = " + str(marital_status)
    session_query = ""
    if session!="":
        session_query += " having count(*) = " + str(session)

    query = "with t as( SELECT username,(select id user_id from auth_user where username=vw_life_skill_education_test.username), village_geocode, village_name, union_geocode, union_name, upazilla_geocode, upazilla_name, district_geocode, district_name, group_type, maritial_status, submission_date, test_type, group_id, adolescent_name, id_adolescent, number_obtained,case when number_obtained::int <=5 then 1 else 0 end poor,case when number_obtained::int >=6 and number_obtained::int <=9 then 1 else 0 end good,case when number_obtained::int >=10 then 1 else 0 end excellent FROM public.vw_life_skill_education_test "+str(filter_query)+"), t1 as( select group_id,count(*) sessions from vw_grp_reg_sessions  group by group_id "+str(session_query)+")select group_id,case when test_type='1' then 'Pre' else 'Post' end test_type,submission_date,count(adolescent_name) enrolled,sum(poor) poor,sum(good) good,sum(excellent) excellent from t where group_id in (select group_id from t1) group by submission_date,poor,test_type,group_id"
    test_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)

    query_for_chart = "with t as( SELECT username, village_geocode, village_name, union_geocode, union_name, upazilla_geocode, upazilla_name, district_geocode, district_name, group_type, maritial_status, submission_date, test_type, group_id, adolescent_name, id_adolescent, number_obtained,case when number_obtained::int <=5 then 1 else 0 end poor,case when number_obtained::int >=6 and number_obtained::int <=9 then 1 else 0 end good,case when number_obtained::int >=10 then 1 else 0 end excellent FROM public.vw_life_skill_education_test "+str(filter_query)+"), t1 as( select group_id,count(*) sessions from vw_grp_reg_sessions  group by group_id "+str(session_query)+")select test_type,sum(poor) poor,sum(good) good,sum(excellent) excellent from t where group_id in (select group_id from t1) group by test_type order by test_type"
    print(query_for_chart)
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
    query = "with t as( select * from plan_mis_report_district_form where pngo_id in "+str(org)+")select 'Number of adolescents girls trained' as cat_name,coalesce(sum(female_girls_unmarried)+sum(female_girls_married),0) summation from t where activity_id = '164' union all select 'Number of adolescents supported to find employment',coalesce(sum(male_boys_unmarried)+sum(male_boys_married)+sum(female_girls_unmarried)+sum(female_girls_married),0) from t where activity_id = '265' union all select 'Number of adolescents supported for enterprise development',coalesce(sum(male_boys_unmarried)+sum(male_boys_married)+sum(female_girls_unmarried)+sum(female_girls_married),0) from t where activity_id = '366' union all select 'Number of adolescents supported for IT and telemedicine work',coalesce(sum(male_boys_unmarried)+sum(male_boys_married)+sum(female_girls_unmarried)+sum(female_girls_married),0) from t where activity_id = '467'"
    economic_empowerment_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    chartvalue = df.summation.tolist()


    query = "select * from usermodule_catchment_area where user_id = "+str(request.user.id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    if df.empty:
        query = "select id,field_name from geo_data where field_type_id = 88"
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        upz_id = df.id.tolist()
        upz_name = df.field_name.tolist()
        upazila = zip(upz_id, upz_name)
    else:
        query = "select id,field_name from geo_data where field_type_id = 88 and id="+str(df.geoid.tolist()[0])
        df = pandas.DataFrame()
        df = pandas.read_sql(query, connection)
        upz_id = df.id.tolist()
        upz_name = df.field_name.tolist()
        upazila = zip(upz_id, upz_name)
    return render(request, 'planmodule/economic_empowerment_report.html', {
        'economic_empowerment_list': economic_empowerment_list,'upazila':upazila,'chartvalue':chartvalue
    })


@login_required
def getEconomicData(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    upazila = request.POST.get('upazila')
    pngo = request.POST.get('pngo')
    filter_query = "where  activity_date between '" + str(from_date) + "' and '" + str(to_date) + "'"

    if upazila !="":
        filter_query += " and upazilla = "+str(upazila)
    if pngo !="":
        filter_query += " and pngo_id = "+str(pngo)

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
    return HttpResponseRedirect("/planmodule/dca_list/")


@login_required
def delete_dca_form(request, dca_id):
    delete_query = "delete from plan_dca where id = " + str(dca_id) + ""
    __db_commit_query(delete_query)
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
            query = "SELECT id, activity_date, activity_type, CASE WHEN activity_type = 1 THEN 'Central Level' WHEN activity_type = 2 THEN 'District Level' ELSE 'Upazilla Level' END activity_type_name, activity_id,(select activity_name from public.plan_activities where activity_value = activity_id limit 1) activity_name, number_of_activity, male_boys_unmarried, male_boys_married, female_girls_unmarried, female_girls_married, comments, pngo_id, (select organization from public.usermodule_organizations where id = pngo_id) pngo_name, district district_id, coalesce((select field_name from geo_data where id = district),'') district_name, upazilla upazilla_id, coalesce((select field_name from geo_data where id = upazilla ),'') upazilla_name FROM plan_mis_report_district_form where activity_type = 3 and upazilla = "+str(geoid)+" and pngo_id in " + str(org)
        else:
            query = "SELECT id, activity_date, activity_type, CASE WHEN activity_type = 1 THEN 'Central Level' WHEN activity_type = 2 THEN 'District Level' ELSE 'Upazilla Level' END activity_type_name, activity_id,(select activity_name from public.plan_activities where activity_value = activity_id limit 1) activity_name, number_of_activity, male_boys_unmarried, male_boys_married, female_girls_unmarried, female_girls_married, comments, pngo_id, (select organization from public.usermodule_organizations where id = pngo_id) pngo_name, district district_id, coalesce((select field_name from geo_data where id = district),'') district_name, upazilla upazilla_id, coalesce((select field_name from geo_data where id = upazilla ),'') upazilla_name FROM plan_mis_report_district_form where district is not null and pngo_id in " + str(org)
    else:
        query = "SELECT id, activity_date, activity_type, CASE WHEN activity_type = 1 THEN 'Central Level' WHEN activity_type = 2 THEN 'District Level' ELSE 'Upazilla Level' END activity_type_name, activity_id,(select activity_name from public.plan_activities where activity_value = activity_id limit 1) activity_name, number_of_activity, male_boys_unmarried, male_boys_married, female_girls_unmarried, female_girls_married, comments, pngo_id, (select organization from public.usermodule_organizations where id = pngo_id) pngo_name, district district_id, coalesce((select field_name from geo_data where id = district),'') district_name, upazilla upazilla_id, coalesce((select field_name from geo_data where id = upazilla ),'') upazilla_name FROM plan_mis_report_district_form where pngo_id in " + str(org)
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
    org_id_list = [org.pk for org in all_organizations]
    org = str(map(str, org_id_list))
    org = org.replace('[', '(').replace(']', ')')
    query = "SELECT DISTINCT ON(data_id) data_id, pngo pngo_name, (SELECT field_name FROM geo_data WHERE geocode = upazila) AS upazila_name, (SELECT field_name FROM geo_data WHERE geocode = union_name) AS union_name, date AS orientation_date, CASE orientation_type WHEN '1' THEN 'কমিউনিটি ওরিয়েন্টেশন' WHEN '2' THEN 'ধর্মীয় নেতা'  WHEN '3' THEN  'বিবাহিত কিশোরী / দম্পত্তি ওরিয়েন্টেশন' WHEN '4' THEN 'ইস্যুভিত্তিক মিটিং'  END AS orientation_type FROM vw_comm_orientation where pngo in (select organization from usermodule_organizations where id::text in" + str(org)+" )"
    community_orientation_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return render(request, 'planmodule/community_orientation_list.html', {
        'community_orientation_list': community_orientation_list
    })

@login_required
def delete_community_orientation(request, data_id):
    delete_query = "update logger_instance set deleted_at = now() where xform_id = 564 and id = " + str(data_id)
    __db_commit_query(delete_query)
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
        query = "select activity_value,activity_name from public.plan_activities where activity_type = 2"
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

        user_id = request.user.id
        pngo_id = current_user.organisation_name_id
        query = "select geoid from public.usermodule_catchment_area where user_id ="+str(user_id)
        df = pandas.DataFrame()
        df = pandas.read_sql(query,connection)
        if df.empty:
            activity_type = 1
        else:
            geoid = df.geoid.tolist()[0]
            query = "select field_type_id from geo_data where id ="+str(geoid)
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            field_type_id = df.field_type_id.tolist()[0]
            if field_type_id == 86:
                activity_type = 2
                district = geoid
            elif field_type_id == 88:
                activity_type = 3
                query = "select id from geo_data where field_parent_id =" + str(geoid)
                df = pandas.DataFrame()
                df = pandas.read_sql(query, connection)
                district = df.id.tolist()[0]
                upazilla = geoid

        if activity_type == 1:
            insert_query = "INSERT INTO public.plan_mis_report_district_form(activity_date, activity_type, activity_id, number_of_activity, male_boys_unmarried, male_boys_married, female_girls_unmarried, female_girls_married, comments, pngo_id) VALUES('"+str(activity_date)+"', "+str(activity_type)+", '"+str(activity_id)+"', "+str(number_of_activity)+", "+str(male_boys_unmarried)+", "+str(male_boys_married)+", "+str(female_girls_unmarried)+", "+str(female_girls_married)+",'"+str(comments)+"', "+str(pngo_id)+")"
        elif activity_type == 2:
            insert_query = "INSERT INTO public.plan_mis_report_district_form(activity_date, activity_type, activity_id, number_of_activity, male_boys_unmarried, male_boys_married, female_girls_unmarried, female_girls_married, comments, pngo_id, district) VALUES('" + str(
                activity_date) + "', " + str(activity_type) + ", '" + str(activity_id) + "', " + str(
                number_of_activity) + ", " + str(male_boys_unmarried) + ", " + str(male_boys_married) + ", " + str(
                female_girls_unmarried) + ", " + str(female_girls_married) + ",'" + str(comments) + "', " + str(
                pngo_id) + "," + str(district) + ")"
        elif activity_type == 3:
            insert_query = "INSERT INTO public.plan_mis_report_district_form(activity_date, activity_type, activity_id, number_of_activity, male_boys_unmarried, male_boys_married, female_girls_unmarried, female_girls_married, comments, pngo_id, district, upazilla) VALUES('" + str(
                activity_date) + "', " + str(activity_type) + ", '" + str(activity_id) + "', " + str(
                number_of_activity) + ", " + str(male_boys_unmarried) + ", " + str(male_boys_married) + ", " + str(
                female_girls_unmarried) + ", " + str(female_girls_married) + ",'" + str(comments) + "', " + str(
                pngo_id) + "," + str(district) + ", " + str(upazilla) + ")"
        __db_commit_query(insert_query)
    return HttpResponseRedirect("/planmodule/mis_report_district_list/")



@login_required
def edit_mis_report_district_form(request, mis_report_id):
    query = "SELECT id, activity_date, activity_type, CASE WHEN activity_type = 1 THEN 'Central Level' WHEN activity_type = 2 THEN 'District Level' ELSE 'Upazilla Level' END activity_type_name, activity_id,(select activity_name from public.plan_activities where activity_value = activity_id) activity_name, number_of_activity, male_boys_unmarried, male_boys_married, female_girls_unmarried, female_girls_married, comments, pngo_id, (select organization from public.usermodule_organizations where id = pngo_id) pngo_name, district district_id, coalesce((select field_name from geo_data where id = district),'') district_name, upazilla upazilla_id, coalesce((select field_name from geo_data where id = upazilla ),'') upazilla_name FROM plan_mis_report_district_form  where id=" + str(mis_report_id)
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
        query = "select activity_value,activity_name from public.plan_activities where activity_type = 2"
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
        update_query = "UPDATE public.plan_mis_report_district_form SET activity_date='"+str(activity_date)+"', activity_id="+str(activity_id)+", number_of_activity="+str(number_of_activity)+", male_boys_unmarried="+str(male_boys_unmarried)+", male_boys_married="+str(male_boys_married)+", female_girls_unmarried="+str(female_girls_unmarried)+", female_girls_married="+str(female_girls_married)+", comments='"+str(comments)+"' WHERE id="+str(mis_report_id)
        __db_commit_query(update_query)
    return HttpResponseRedirect("/planmodule/mis_report_district_list/")


@login_required
def delete_mis_report_district_form(request, mis_report_id):
    delete_query = "delete from plan_mis_report_district_form where id = " + str(mis_report_id) + ""
    __db_commit_query(delete_query)
    return HttpResponseRedirect("/planmodule/mis_report_district_list/")