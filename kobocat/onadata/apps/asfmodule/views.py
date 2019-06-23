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
from django.template.loader import render_to_string
import os
from onadata.apps.usermodule.views import error_page

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

def quryExecution(query):
    cursor = connection.cursor()
    cursor.execute(query)
    value = cursor.fetchone()
    cursor.close()
    return value

def index(request):
    id_string = 'child_marriage_prevention_reg'
    query = "SELECT id, uuid  FROM logger_xform where id_string = 'child_marriage_prevention_reg'"
    queryResult = quryExecution(query)
    xform_id = queryResult[0]
    form_uuid = str(queryResult[1])
    username = request.user.username
    select_data = json.dumps(__db_fetch_values_dict(
        "select replace(field_name,'/','__') as field_name,value_text,value_label as bn_label from xform_extracted where xform_id = (select id from public.logger_xform where id_string = '" + str(
            id_string) + "') and field_type in ('select one','select all that apply') "))
    print()
    return render(request, "asfmodule/index.html",
                  {'id_string': id_string, 'xform_id': xform_id,
                   'form_uuid': form_uuid, 'username': username, 'select_data': select_data,
                   })
    # return render(request, 'asfmodule/index.html')


def profile_view(request,victim_id):
    current_user = UserModuleProfile.objects.get(user_id=request.user.id)
    role = UserRoleMap.objects.get(user=current_user.pk)
    role_id = role.role.pk
    query =""" SELECT distinct '<div class="row"> <div class="col-lg-11"> <div class="clearfix"></div> <div class="panel-group"  role="tablist" aria-multiselectable="true"><div class="panel panel-default"><div class="panel-heading" role="tab" id="heading'||category_id||'"><h4 class="panel-title"><a class="collapsed"  onclick="load_forms('|| category_id ||',''internal_accordian'|| category_id ||''')" role="button" data-toggle="collapse"  href="#collapse'|| category_id ||'" aria-expanded="false" aria-controls="collapse'|| category_id ||'"> ' ||(SELECT category_name FROM forms_categories WHERE id = fc.category_id :: INT) || ' </a> </h4></div><div id="collapse'|| category_id ||'" class="panel-collapse collapse" role="tabpanel" aria-labelledby="heading'|| category_id ||'"><div class="panel-body"><div class="panel-group" id="internal_accordian'|| category_id ||'" role="tablist" aria-multiselectable="true"></div></div></div></div></div></div>'|| case when first_value(can_submit)over(PARTITION by category_id ORDER by can_submit desc) = 1 then '<a ng-click="load_forms_list('|| category_id ||')"  class="btn btn-success" id="form'|| category_id ||'"  data-toggle="modal" data-target="#myModal"  >Forms</a>' else '' end  ||'</div>' as form_str FROM rolewiseform rf, forms_categories_relation fc WHERE ( rf.can_view = 1 OR rf.can_submit = 1) AND fc.form_id = rf.xform_id AND role_id = """+ str(role_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query,connection)
    main_str = ""
    for each in df['form_str']:
        main_str += str(each)
    main_str = json.dumps(main_str)

    id_string = 'child_marriage_prevention_reg'
    query = "SELECT id, uuid  FROM logger_xform where id_string = 'child_marriage_prevention_reg'"
    queryResult = quryExecution(query)
    xform_id = queryResult[0]
    form_uuid = str(queryResult[1])
    username = request.user.username


    return render(request, 'asfmodule/profile_view_test.html',{'main_str':main_str, 'victim_id':victim_id,'id_string': id_string, 'xform_id': xform_id,
                   'form_uuid': form_uuid, 'username': username})

@csrf_exempt
def get_forms_data(request):
    category_id = request.POST.get('category_id')
    victim_id = request.POST.get('victim_id')
    user_id = request.user.id
    query = """ WITH t AS( SELECT ( SELECT title FROM logger_xform WHERE id = form_id), form_id FROM vwrolewiseformpermission rf, forms_categories_relation fc WHERE ( rf.can_view = 1 OR rf.can_submit = 1) AND category_id = """ + str(category_id)+ """ AND fc.form_id = rf.xform_id AND user_id = """ + str(user_id)+ """) , t1 AS ( SELECT logger_instance.id log_ins_id, json->>'victim_id'::text victim_id, * FROM t, logger_instance WHERE t.form_id = logger_instance.xform_id order by date_created desc) SELECT '<div class="panel panel-default" ><div class="panel-heading forms_data_panel_heading" role="tab" id="heading' ||log_ins_id ||'"><h4 class="panel-title forms_data_panel_title"><a onclick="load_forms_data(' ||log_ins_id ||',''data_view' || log_ins_id ||''')" role="button" data-toggle="collapse" href="#collapse' || log_ins_id ||'" aria-expanded="false" aria-controls="collapse' ||log_ins_id ||'">' || to_char(date_created::date,'DD/MM/YYYY') ||'</a><span style="margin-left:30%">'|| replace(greatest(title,rpad(title, 32,' '))::text,' ','&nbsp;') ||'</span></h4></div><div id="collapse' || log_ins_id ||'" class="panel-collapse collapse" role="tabpanel" aria-labelledby="heading' || log_ins_id ||'"><div class="panel-body"><div class="ribbon" id="data_view' || log_ins_id ||'"></div></div></div></div>' AS form_str FROM t1 WHERE victim_id LIKE '%""" + str(victim_id) + """%' """
    print(query)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    main_str = ""
    for each in df['form_str']:
        main_str += str(each)
    main_str = json.dumps(main_str)
    return HttpResponse(main_str)


@csrf_exempt
def get_data_view(request):
    username = request.user
    logger_id = request.POST.get('logger_id')
    query = """ select * from public.get_data_detail_view("""+str(logger_id)+""") order by  _re_sl,_sl_no """
    form_data_matrix = json.dumps(__db_fetch_values_dict(query))
    root = "root"+str(logger_id)
    rendered = render_to_string('asfmodule/data_view.html', {
        'form_data_matrix': form_data_matrix,
        'username': username,
        'root':root
    })
    rendered = json.dumps(rendered)
    print(rendered)
    return HttpResponse(rendered)



@csrf_exempt
def get_forms_list(request):
    category_id = request.POST.get('category_id')
    victim_id = request.POST.get('victim_id')
    user_id = request.user.id
    query = """ WITH t AS(SELECT (SELECT title FROM logger_xform WHERE id = form_id), form_id FROM vwrolewiseformpermission rf, forms_categories_relation fc WHERE ( rf.can_submit = 1) AND category_id = """ +str(category_id)+ """ AND fc.form_id = rf.xform_id AND user_id = """+str(user_id)+"""),t1 as(SELECT DISTINCT '<a class="btn btn-outline form-group form-control" onclick="load_forms_html('|| form_id ||')" >'|| title ||'</a><br>' AS popup_str FROM t)select * from t1 order by length(popup_str) asc"""
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    # main_str = """ <ul class="list-group"> """
    # for each in df['popup_str']:
    #     main_str += """ <li class="list-group-item"> """ + str(each) + """ </li> """
    # main_str += """ </ul> """
    main_str = ""
    for each in df['popup_str']:
        main_str += str(each)
    main_str = json.dumps(main_str)
    return HttpResponse(main_str)


@csrf_exempt
def get_forms_html(request):
    form_id = request.GET.get('form_id')
    query = """ select *,(select title from logger_xform where id = form_id limit 1) from odk_web_forms_html where form_id =  """+str(form_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    form_html = df.form_html.tolist()[0]
    dom_tree = df.dom_tree.tolist()[0]
    angular_containers = df.angular_containers.tolist()[0]
    title = df.title.tolist()[0]
    data = {
        'form_html':form_html,
        'dom_tree':dom_tree,
        'angular_containers':angular_containers,
        'title':title

    }
    return HttpResponse(json.dumps(data))

@csrf_exempt
def get_districts(request):
    field_parent_id = request.POST.get('div')
    query = "select id,field_name from geo_data where field_type_id = 86 and field_parent_id = "+str(field_parent_id)
    print(query)
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)

@csrf_exempt
def get_upazilas(request):
    field_parent_id = request.POST.get('dist')
    query = "select id,field_name from geo_data where field_type_id = 88 and field_parent_id = "+str(field_parent_id)
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)

@csrf_exempt
def get_unions(request):
    field_parent_id = request.POST.get('upz')
    query = "select id,field_name from geo_data where field_type_id = 89 and field_parent_id = "+str(field_parent_id)
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)

@csrf_exempt
def get_wards(request):
    field_parent_id = request.POST.get('uni')
    query = "select id,field_name from geo_data where field_type_id = 92 and field_parent_id = "+str(field_parent_id)
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)

def incident_id_generator():
    current_year = datetime.datetime.now().year
    # current year last incident id
    qry = "select incident_id::bigint from asf_case where date_part('year', created_at)='"+str(current_year)+"' order by id desc"
    df = pandas.read_sql(qry,connection)
    if not df.empty:
        incident_id = df.incident_id.tolist()[0]
        incident_id += 1
    else:
        incident_id = str(current_year) + '001'
    return incident_id

@login_required
def case_list(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    query = "select id,incident_id,incident_date,district,status from asf_case"
    case_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return render(request, 'asfmodule/case_list.html', {'case_list': case_list,'divisions':divisions})

@csrf_exempt
def get_case_list(request):
    division = request.POST.get('division')
    district = request.POST.get('district')
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = "select id,incident_id,incident_date,district,status from asf_case where division like '"+str(division)+"' and district like '"+str(district)+"' and to_date(incident_date,'DD/MM/YYYY')::date between to_date('"+str(from_date)+"','DD/MM/YYYY') and to_date('"+str(to_date)+"','DD/MM/YYYY')"
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)

@login_required
def add_case_form(request):
    incident_id = incident_id_generator()
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query,connection)
    divisions = zip(df.id.tolist(),df.field_name.tolist())

    query = "select id,organization org_name from usermodule_organizations"
    df = pandas.read_sql(query, connection)
    organizations = zip(df.id.tolist(),df.org_name.tolist())

    query = "select org_tbl_id,(select organization from usermodule_organizations where id = org_tbl_id::int limit 1) org_name from org_additional_info where org_type = 'Electronics Media'"
    df = pandas.read_sql(query, connection)
    tv_chanels = zip(df.org_tbl_id.tolist(), df.org_name.tolist())

    return render(request, 'asfmodule/add_case_form.html', {
        'incident_id': incident_id, 'divisions': divisions, 'tv_chanels': tv_chanels,'organizations':organizations
    })


@login_required
def insert_case_form(request):
    incident_id = request.POST.get('incident_id')
    incident_date = request.POST.get('incident_date')
    incident_description = request.POST.get('incident_description')
    incident_rural_or_urban = request.POST.get('incident_rural_or_urban')
    division = request.POST.get('division')
    district = request.POST.get('district')
    upazila = request.POST.get('upazila')
    union = request.POST.get('union')
    ward = request.POST.get('ward')
    incidence_address = request.POST.get('incidence_address')
    incidence_post_office = request.POST.get('incidence_post_office')
    information_source = request.POST.get('information_source')
    source_organization_name = request.POST.get('source_organization_name')
    source_name = request.POST.get('source_name')
    source_designation = request.POST.get('source_designation')
    source_address = request.POST.get('source_address')
    source_phone = request.POST.get('source_phone')
    print_media_name = request.POST.get('print_media_name')
    print_media_page_number = request.POST.get('print_media_page_number')
    print_media_reporter_name = request.POST.get('print_media_reporter_name')
    print_media_publishing_date = request.POST.get('print_media_publishing_date')
    electronic_media_name = request.POST.get('electronic_media_name')
    electronic_media_telecast_date = request.POST.get('electronic_media_telecast_date')
    incident_type = request.POST.get('incident_type')
    burn_type = request.POST.get('burn_type')
    incident_cause = request.POST.get('incident_cause')
    people_affected = request.POST.get('people_affected')
    people_died = request.POST.get('people_died')
    if request.FILES:
        myfile = request.FILES['coverage_picture']
        url = "onadata/media/uploaded_files/"
        userName = request.user
        fs = FileSystemStorage(location=url)
        myfile.name = str(datetime.datetime.now()) + "_" + str(userName) + "_" + str(myfile.name)
        filename = fs.save(myfile.name, myfile)
        coverage_picture = "onadata/media/uploaded_files/" + myfile.name
    else: coverage_picture = ''

    victim_id_list = request.POST.getlist('victim_id')
    victim_name_list = request.POST.getlist('victim_name')
    victim_sex_list = request.POST.getlist('victim_sex')
    victim_contact_list = request.POST.getlist('victim_contact')
    victim_address_list = request.POST.getlist('victim_address')

    created_by = request.user.id


    insert_qry = "INSERT INTO public.asf_case(incident_id, incident_date, incident_description, incident_rural_or_urban, division, district, upazila, union_id, ward, incidence_address, incidence_post_office, information_source, source_organization_name, source_name, source_designation, source_address, source_phone, print_media_name, print_media_page_number, print_media_reporter_name, print_media_publishing_date, electronic_media_name, electronic_media_telecast_date, coverage_picture, incident_type, burn_type, incident_cause, people_affected, people_died, created_by,status) values ('"+str(incident_id)+"', '"+str(incident_date)+"' , '"+str(incident_description)+"', '"+str(incident_rural_or_urban)+"', '"+str(division)+"', '"+str(district)+"', '"+str(upazila)+"', '"+str(union)+"', '"+str(ward)+"', '"+str(incidence_address)+"', '"+str(incidence_post_office)+"', '"+str(information_source)+"', '"+str(source_organization_name)+"', '"+str(source_name)+"', '"+str(source_designation)+"', '"+str(source_address)+"', '"+str(source_phone)+"', '"+str(print_media_name)+"', '"+str(print_media_page_number)+"', '"+str(print_media_reporter_name)+"', '"+str(print_media_publishing_date)+"', '"+str(electronic_media_name)+"', '"+str(electronic_media_telecast_date)+"', '"+str(coverage_picture)+"', '"+str(incident_type)+"', '"+str(burn_type)+"', '"+str(incident_cause)+"', '"+str(people_affected)+"', '"+str(people_died)+"', "+str(created_by)+",'New') returning id"
    case_id = __db_fetch_single_value(insert_qry)

    for victim_id,victim_name,victim_sex,victim_contact,victim_address in zip(victim_id_list,victim_name_list,victim_sex_list,victim_contact_list,victim_address_list):
        ins_qry = "insert into asf_victim(case_id,victim_id,victim_name,sex,mobile,current_address)values('"+str(case_id)+"','"+str(victim_id)+"','"+str(victim_name)+"','"+str(victim_sex)+"','"+str(victim_contact)+"','"+str(victim_address)+"')"
        __db_commit_query(ins_qry)
    return HttpResponseRedirect('/asf/case_list/')


@login_required
def case_detail(request,case_id):
    qry = "select incident_id,incident_date,incident_description,(select field_name from geo_data where id = division::bigint limit 1)division, (select field_name from geo_data where id = district::bigint limit 1)district, (select field_name from geo_data where id = upazila::bigint limit 1)upazila, case when union_id ='' then '' else (select field_name from geo_data where id = union_id::bigint limit 1) end union_name,status from asf_case where id ="+str(case_id)
    df = pandas.read_sql(qry,connection)
    if df.empty:
        return error_page(request, "No Data")

    incident_id = df.incident_id.tolist()[0] if len(df.incident_id.tolist()) else ''
    incident_date = df.incident_date.tolist()[0] if len(df.incident_date.tolist()) else ''
    incident_description = df.incident_description.tolist()[0] if len(df.incident_description.tolist()) else ''
    division = df.division.tolist()[0] if len(df.division.tolist()) else ''
    district = df.district.tolist()[0] if len(df.district.tolist()) else ''
    upazila = df.upazila.tolist()[0] if len(df.upazila.tolist()) else ''
    union_name = df.union_name.tolist()[0] if len(df.union_name.tolist()) else ''
    status = df.status.tolist()[0] if len(df.status.tolist()) else ''

    return render(request, "asfmodule/case_detail.html", {
        'case_id': case_id,
        'incident_id': incident_id,
        'incident_date':  incident_date,
        'incident_description': incident_description,
        'division': division,
        'district': district,
        'upazila': upazila,
        'union_name': union_name,
        'status': status
    })


@csrf_exempt
def update_case_status(request,case_id):
    status = request.POST.get('status')
    update_qry = "update asf_case set status = '"+str(status)+"' where id="+str(case_id)
    __db_commit_query(update_qry)
    messages.success(request, '<i class="fa fa-check-circle"></i> Case status has been updated successfully!',extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect('/asf/case_detail/'+str(case_id))

@csrf_exempt
def get_victim_list(request):
    case_id = request.POST.get('case_id')
    query = "select id,victim_id,victim_name,mobile,sex,status,(select status from asf_case where id = case_id::int limit 1) case_status from asf_victim where case_id::int = "+str(case_id)
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)

@login_required
def add_victim(request,case_id):
    qry = "select victim_id::bigint from asf_victim where case_id::int = "+str(case_id)+" order by victim_id::bigint desc"
    df = pandas.read_sql(qry, connection)

    victim_id = df.victim_id.tolist()[0]
    victim_id += 1

    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())

    return render(request, 'asfmodule/add_victim_form.html', {
    'victim_id':victim_id,'divisions':divisions,'case_id':case_id
    })


@login_required
def insert_victim(request,case_id):
    victim_id = request.POST.get('victim_id')
    victim_name = request.POST.get('victim_name')
    victim_sex = request.POST.get('victim_sex')
    birth_date = request.POST.get('birth_date')
    victim_age = request.POST.get('victim_age')
    mobile = request.POST.get('mobile')
    mobile2 = request.POST.get('mobile2')
    any_nid_brn_passport = request.POST.get('any_nid_brn_passport')
    nid_brn_passport = request.POST.get('nid_brn_passport')
    education = request.POST.get('education')
    occupation = request.POST.get('occupation')
    maritial_status = request.POST.get('maritial_status')
    father_name = request.POST.get('father_name')
    mother_name = request.POST.get('mother_name')
    spouse_name = request.POST.get('spouse_name')
    current_division = request.POST.get('current_division')
    current_district = request.POST.get('current_district')
    current_upazila = request.POST.get('current_upazila')
    current_union = request.POST.get('current_union')
    current_ward = request.POST.get('current_ward')
    current_address = request.POST.get('current_address')
    current_postoffice = request.POST.get('current_postoffice')
    present_permanent_address_same = request.POST.get('present_permanent_address_same')
    permanent_division= request.POST.get('permanent_division')
    permanent_district = request.POST.get('permanent_district')
    permanent_upazila = request.POST.get('permanent_upazila')
    permanent_union = request.POST.get('permanent_union')
    permanent_ward = request.POST.get('permanent_ward')
    permanent_address = request.POST.get('permanent_address')
    permanent_postoffice = request.POST.get('permanent_postoffice')
    injury_details = request.POST.get('injury_details')
    notified_within_24h = request.POST.get('notified_within_24h')
    verification_within_24h = request.POST.get('verification_within_24h')
    brought_asf_within_48h = request.POST.get('brought_asf_within_48h')

    if request.FILES:
        myfile = request.FILES['picture']
        url = "onadata/media/uploaded_files/"
        userName = request.user
        fs = FileSystemStorage(location=url)
        myfile.name = str(datetime.datetime.now()) + "_" + str(userName) + "_" + str(myfile.name)
        filename = fs.save(myfile.name, myfile)
        picture = "onadata/media/uploaded_files/" + myfile.name
    else: picture = ''


    created_by = request.user.id
    insert_qry = "INSERT INTO public.asf_victim (victim_id, victim_name, sex, birth_date, victim_age, mobile, mobile2, any_nid_brn_passport, nid_brn_passport, education, occupation, maritial_status, father_name, mother_name, spouse_name, picture, current_division, current_district, current_upazila, current_union, current_ward, current_address, current_postoffice, present_permanent_address_same,permanent_division,permanent_district, permanent_upazila, permanent_union, permanent_ward, permanent_address, permanent_postoffice, injury_details, notified_within_24h, verification_within_24h, brought_asf_within_48h, created_by, case_id) VALUES('"+str(victim_id)+"', '"+str(victim_name)+"', '"+str(victim_sex)+"', '"+str(birth_date)+"', '"+str(victim_age)+"', '"+str(mobile)+"', '"+str(mobile2)+"', '"+str(any_nid_brn_passport)+"', '"+str(nid_brn_passport)+"', '"+str(education)+"', '"+str(occupation)+"', '"+str(maritial_status)+"', '"+str(father_name)+"', '"+str(mother_name)+"', '"+str(spouse_name)+"', '"+str(picture)+"', '"+str(current_division)+"', '"+str(current_district)+"', '"+str(current_upazila)+"', '"+str(current_union)+"', '"+str(current_ward)+"', '"+str(current_address)+"', '"+str(current_postoffice)+"', '"+str(present_permanent_address_same)+"', '"+str(permanent_division)+"', '"+str(permanent_district)+"', '"+str(permanent_upazila)+"', '"+str(permanent_union)+"', '"+str(permanent_ward)+"', '"+str(permanent_address)+"', '"+str(permanent_postoffice)+"', '"+str(injury_details)+"', '"+str(notified_within_24h)+"', '"+str(verification_within_24h)+"', '"+str(brought_asf_within_48h)+"' , "+str(created_by)+", '"+str(case_id)+"')"
    __db_commit_query(insert_qry)
    messages.success(request, '<i class="fa fa-check-circle"></i> New Victim has been added successfully!',
                     extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect('/asf/case_detail/'+str(case_id)+'/')

@login_required
def edit_victim(request,victim_tbl_id):
    qry = "select * from asf_victim where id = "+str(victim_tbl_id)
    df = pandas.read_sql(qry,connection)
    victim_id = df.victim_id.tolist()[0] if len(df.victim_id.tolist()) and df.victim_id.tolist()[0] is not None  else ''
    victim_name = df.victim_name.tolist()[0] if len(df.victim_name.tolist()) and df.victim_name.tolist()[0] is not None  else ''
    victim_sex = df.sex.tolist()[0] if len(df.sex.tolist()) and df.sex.tolist()[0] is not None  else ''
    birth_date = df.birth_date.tolist()[0] if len(df.birth_date.tolist()) and df.birth_date.tolist()[0] is not None  else ''
    victim_age = df.victim_age.tolist()[0] if len(df.victim_age.tolist()) and df.victim_age.tolist()[0] is not None  else ''
    mobile = df.mobile.tolist()[0] if len(df.mobile.tolist()) and df.mobile.tolist()[0] is not None  else ''
    mobile2 = df.mobile2.tolist()[0] if len(df.mobile2.tolist()) and df.mobile2.tolist()[0] is not None  else ''
    any_nid_brn_passport = df.any_nid_brn_passport.tolist()[0] if len(df.any_nid_brn_passport.tolist()) and df.any_nid_brn_passport.tolist()[0] is not None  else ''
    nid_brn_passport = df.nid_brn_passport.tolist()[0] if len(df.nid_brn_passport.tolist()) and df.nid_brn_passport.tolist()[0] is not None  else ''
    education = df.education.tolist()[0] if len(df.education.tolist()) and df.education.tolist()[0] is not None  else ''
    occupation = df.occupation.tolist()[0] if len(df.occupation.tolist()) and df.occupation.tolist()[0] is not None  else ''
    maritial_status = df.maritial_status.tolist()[0] if len(df.maritial_status.tolist()) and df.maritial_status.tolist()[0] is not None  else ''
    father_name = df.father_name.tolist()[0] if len(df.father_name.tolist()) and df.father_name.tolist()[0] is not None  else ''
    mother_name = df.mother_name.tolist()[0] if len(df.mother_name.tolist()) and df.mother_name.tolist()[0] is not None  else ''
    spouse_name = df.spouse_name.tolist()[0] if len(df.spouse_name.tolist()) and df.spouse_name.tolist()[0] is not None  else ''
    picture = df.picture.tolist()[0] if len(df.picture.tolist()) and df.picture.tolist()[0] is not None  else ''

    current_division = df.current_division.tolist()[0] if len(df.current_division.tolist()) and df.current_division.tolist()[0] is not None  else '%'
    current_district = df.current_district.tolist()[0] if len(df.current_district.tolist()) and df.current_district.tolist()[0] is not None  else '%'
    current_upazila = df.current_upazila.tolist()[0] if len(df.current_upazila.tolist()) and df.current_upazila.tolist()[0] is not None  else '%'
    current_union = df.current_union.tolist()[0] if len(df.current_union.tolist()) and df.current_union.tolist()[0] is not None  else '%'
    current_ward = df.current_ward.tolist()[0] if len(df.current_ward.tolist()) and df.current_ward.tolist()[0] is not None  else '%'
    current_address = df.current_address.tolist()[0] if len(df.current_address.tolist()) and df.current_address.tolist()[0] is not None  else ''
    current_postoffice = df.current_postoffice.tolist()[0] if len(df.current_postoffice.tolist()) and df.current_postoffice.tolist()[0] is not None  else ''
    present_permanent_address_same = df.present_permanent_address_same.tolist()[0] if len(df.present_permanent_address_same.tolist()) and df.present_permanent_address_same.tolist()[0] is not None  else ''
    permanent_division = df.permanent_division.tolist()[0] if len(df.permanent_division.tolist()) and df.permanent_division.tolist()[0] is not None  else '%'
    permanent_district = df.permanent_district.tolist()[0] if len(df.permanent_district.tolist()) and df.permanent_district.tolist()[0] is not None  else '%'
    permanent_upazila = df.permanent_upazila.tolist()[0] if len(df.permanent_upazila.tolist()) and df.permanent_upazila.tolist()[0] is not None  else '%'
    permanent_union = df.permanent_union.tolist()[0] if len(df.permanent_union.tolist()) and df.permanent_union.tolist()[0] is not None  else '%'
    permanent_ward = df.permanent_ward.tolist()[0] if len(df.permanent_ward.tolist()) and df.permanent_ward.tolist()[0] is not None  else '%'
    permanent_address = df.permanent_address.tolist()[0] if len(df.permanent_address.tolist()) and df.permanent_address.tolist()[0] is not None  else ''
    permanent_postoffice = df.permanent_postoffice.tolist()[0] if len(df.permanent_postoffice.tolist()) and df.permanent_postoffice.tolist()[0] is not None  else ''
    injury_details = df.injury_details.tolist()[0] if len(df.injury_details.tolist()) and df.injury_details.tolist()[0] is not None  else ''
    notified_within_24h = df.notified_within_24h.tolist()[0] if len(df.notified_within_24h.tolist()) and df.notified_within_24h.tolist()[0] is not None  else ''
    verification_within_24h = df.verification_within_24h.tolist()[0] if len(df.verification_within_24h.tolist()) and df.verification_within_24h.tolist()[0] is not None  else ''
    brought_asf_within_48h = df.brought_asf_within_48h.tolist()[0] if len(df.brought_asf_within_48h.tolist()) and df.brought_asf_within_48h.tolist()[0] is not None  else ''

    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())

    query = "select id,field_name from geo_data where field_type_id = 86 and field_parent_id::text like '"+str(current_division)+"'"
    df = pandas.read_sql(query, connection)
    current_districts = zip(df.id.tolist(), df.field_name.tolist())

    query = "select id,field_name from geo_data where field_type_id = 86 and field_parent_id::text like '" + str(
        permanent_division) + "'"
    df = pandas.read_sql(query, connection)
    permanent_districts = zip(df.id.tolist(), df.field_name.tolist())

    query = "select id,field_name from geo_data where field_type_id = 88 and field_parent_id::text like '" + str(
        current_district) + "'"
    df = pandas.read_sql(query, connection)
    current_upazilas = zip(df.id.tolist(), df.field_name.tolist())

    query = "select id,field_name from geo_data where field_type_id = 88 and field_parent_id::text like '" + str(
        permanent_district) + "'"
    df = pandas.read_sql(query, connection)
    permanent_upazilas = zip(df.id.tolist(), df.field_name.tolist())

    query = "select id,field_name from geo_data where field_type_id = 89 and field_parent_id::text like '" + str(
        current_upazila) + "'"
    df = pandas.read_sql(query, connection)
    current_unions = zip(df.id.tolist(), df.field_name.tolist())

    query = "select id,field_name from geo_data where field_type_id = 89 and field_parent_id::text like '" + str(
        permanent_upazila) + "'"
    df = pandas.read_sql(query, connection)
    permanent_unions = zip(df.id.tolist(), df.field_name.tolist())

    query = "select id,field_name from geo_data where field_type_id = 92 and field_parent_id::text like '" + str(
        current_union) + "'"
    df = pandas.read_sql(query, connection)
    current_wards = zip(df.id.tolist(), df.field_name.tolist())

    query = "select id,field_name from geo_data where field_type_id = 92 and field_parent_id::text like '" + str(
        permanent_union) + "'"
    df = pandas.read_sql(query, connection)
    permanent_wards = zip(df.id.tolist(), df.field_name.tolist())

    return render(request, 'asfmodule/edit_victim_form.html', {
        'divisions':divisions,
        'current_districts':current_districts,
        'permanent_districts':permanent_districts,
        'permanent_division':permanent_division,
        'current_upazilas':current_upazilas,
        'permanent_upazilas':permanent_upazilas,
        'current_unions':current_unions,
        'permanent_unions':permanent_unions,
        'current_wards':current_wards,
        'permanent_wards':permanent_wards,
        'victim_tbl_id':victim_tbl_id,
        'victim_id':victim_id,
        'victim_name':victim_name,
        'victim_sex':victim_sex,
        'birth_date':birth_date,
        'victim_age':victim_age,
        'mobile':mobile,
        'mobile2':mobile2,
        'any_nid_brn_passport':any_nid_brn_passport,
        'nid_brn_passport':nid_brn_passport,
        'education':education,
        'occupation':occupation,
        'maritial_status':maritial_status,
        'father_name':father_name,
        'mother_name':mother_name,
        'spouse_name':spouse_name,
        'picture':picture,
        'current_division':current_division,
        'current_district':current_district,
        'current_upazila':current_upazila,
        'current_union':current_union,
        'current_ward':current_ward,
        'current_address':current_address,
        'current_postoffice':current_postoffice,
        'present_permanent_address_same':present_permanent_address_same,
        'permanent_district':permanent_district,
        'permanent_upazila':permanent_upazila,
        'permanent_union':permanent_union,
        'permanent_ward':permanent_ward,
        'permanent_address':permanent_address,
        'permanent_postoffice':permanent_postoffice,
        'injury_details':injury_details,
        'notified_within_24h':notified_within_24h,
        'verification_within_24h':verification_within_24h,
        'brought_asf_within_48h':brought_asf_within_48h
    })


@login_required
def update_victim(request,victim_tbl_id):
    case_id = __db_fetch_single_value("select case_id from asf_victim where id = "+str(victim_tbl_id))
    victim_id = request.POST.get('victim_id')
    victim_name = request.POST.get('victim_name')
    victim_sex = request.POST.get('victim_sex')
    birth_date = request.POST.get('birth_date')
    victim_age = request.POST.get('victim_age')
    mobile = request.POST.get('mobile')
    mobile2 = request.POST.get('mobile2')
    any_nid_brn_passport = request.POST.get('any_nid_brn_passport')
    nid_brn_passport = request.POST.get('nid_brn_passport')
    education = request.POST.get('education')
    occupation = request.POST.get('occupation')
    maritial_status = request.POST.get('maritial_status')
    father_name = request.POST.get('father_name')
    mother_name = request.POST.get('mother_name')
    spouse_name = request.POST.get('spouse_name')
    current_division = request.POST.get('current_division')
    current_district = request.POST.get('current_district')
    current_upazila = request.POST.get('current_upazila')
    current_union = request.POST.get('current_union')
    current_ward = request.POST.get('current_ward')
    current_address = request.POST.get('current_address')
    current_postoffice = request.POST.get('current_postoffice')
    present_permanent_address_same = request.POST.get('present_permanent_address_same')
    permanent_division = request.POST.get('permanent_division')
    permanent_district = request.POST.get('permanent_district')
    permanent_upazila = request.POST.get('permanent_upazila')
    permanent_union = request.POST.get('permanent_union')
    permanent_ward = request.POST.get('permanent_ward')
    permanent_address = request.POST.get('permanent_address')
    permanent_postoffice = request.POST.get('permanent_postoffice')
    injury_details = request.POST.get('injury_details')
    notified_within_24h = request.POST.get('notified_within_24h')
    verification_within_24h = request.POST.get('verification_within_24h')
    brought_asf_within_48h = request.POST.get('brought_asf_within_48h')

    if request.FILES:
        myfile = request.FILES['picture']
        url = "onadata/media/uploaded_files/"
        userName = request.user
        fs = FileSystemStorage(location=url)
        myfile.name = str(datetime.datetime.now()) + "_" + str(userName) + "_" + str(myfile.name)
        filename = fs.save(myfile.name, myfile)
        picture = "onadata/media/uploaded_files/" + myfile.name
    else:
        picture = ''

    created_by = request.user.id

    updt_qry = "UPDATE public.asf_victim SET victim_id='"+str(victim_id)+"', victim_name='"+str(victim_name)+"', sex='"+str(victim_sex)+"', birth_date='"+str(birth_date)+"', victim_age='"+str(victim_age)+"', mobile='"+str(mobile)+"', mobile2='"+str(mobile2)+"', any_nid_brn_passport='"+str(any_nid_brn_passport)+"', nid_brn_passport='"+str(nid_brn_passport)+"', education='"+str(education)+"', occupation='"+str(occupation)+"', maritial_status='"+str(maritial_status)+"', father_name='"+str(father_name)+"', mother_name='"+str(mother_name)+"', spouse_name='"+str(spouse_name)+"', picture='"+str(picture)+"', current_division='"+str(current_division)+"', current_district='"+str(current_district)+"', current_upazila='"+str(current_upazila)+"', current_union='"+str(current_union)+"', current_ward='"+str(current_ward)+"', current_address='"+str(current_address)+"', current_postoffice='"+str(current_postoffice)+"', present_permanent_address_same='"+str(present_permanent_address_same)+"', permanent_division='"+str(permanent_division)+"', permanent_district='"+str(permanent_district)+"', permanent_upazila='"+str(permanent_upazila)+"', permanent_union='"+str(permanent_union)+"', permanent_ward='"+str(permanent_ward)+"', permanent_address='"+str(permanent_address)+"', permanent_postoffice='"+str(permanent_postoffice)+"', injury_details='"+str(injury_details)+"', notified_within_24h='"+str(notified_within_24h)+"', verification_within_24h='"+str(verification_within_24h)+"', brought_asf_within_48h='"+str(brought_asf_within_48h)+"', created_by = '"+str(created_by)+"' where id = "+str(victim_tbl_id)
    __db_commit_query(updt_qry)
    messages.success(request, '<i class="fa fa-check-circle"></i> Victim Info has been updated successfully!',
                     extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect('/asf/case_detail/' + str(case_id) + '/')

@login_required
def victim_status(request,victim_tbl_id):
    if request.POST:
        case_id = __db_fetch_single_value("select case_id from asf_victim where id = " + str(victim_tbl_id))
        status = request.POST.get('status')
        reason_of_not_adoption = request.POST.get('reason_of_not_adoption')
        victim_status_comment = request.POST.get('victim_status_comment')
        updt_qry = "UPDATE public.asf_victim SET status='" + str(status) + "',reason_of_not_adoption='" + str(reason_of_not_adoption) + "',victim_status_comment='" + str(victim_status_comment) + "' where id = " + str(victim_tbl_id)
        __db_commit_query(updt_qry)
        messages.success(request, '<i class="fa fa-check-circle"></i> Victim Status has been updated successfully!',
                         extra_tags='alert-success crop-both-side')
        return HttpResponseRedirect('/asf/case_detail/' + str(case_id) + '/')
    return render(request, 'asfmodule/victim_status_form.html',{'victim_tbl_id':victim_tbl_id})

@login_required
def refer_victim(request,victim_tbl_id):
    if request.POST:
        case_id = __db_fetch_single_value("select case_id from asf_victim where id = " + str(victim_tbl_id))
        referred_date = request.POST.get('referred_date')
        referred_phone = request.POST.get('referred_phone')
        referred_service = request.POST.get('referred_service')
        referred_organization = request.POST.get('referred_organization')
        referred_comment = request.POST.get('referred_comment')
        updt_qry = "UPDATE public.asf_victim SET referred_date='" + str(referred_date) + "',referred_phone='" + str(referred_phone) + "',referred_service='" + str(referred_service) + "',referred_organization='" + str(referred_organization) + "',referred_comment='" + str(referred_comment) + "' where id = " + str(victim_tbl_id)
        __db_commit_query(updt_qry)
        messages.success(request, '<i class="fa fa-check-circle"></i> Victim Status has been updated successfully!',
                         extra_tags='alert-success crop-both-side')
        return HttpResponseRedirect('/asf/case_detail/' + str(case_id) + '/')

    query = "select id,organization org_name from usermodule_organizations"
    df = pandas.read_sql(query, connection)
    organizations = zip(df.id.tolist(), df.org_name.tolist())
    return render(request, 'asfmodule/victim_refer_form.html', {'victim_tbl_id': victim_tbl_id,'organizations':organizations})

@login_required
def victim_profile(request,victim_tbl_id):
    qry = "SELECT *,(select field_name from geo_data where id = current_division::bigint limit 1) current_division ,(select field_name from geo_data where id = current_district::bigint limit 1) current_district ,(select field_name from geo_data where id = current_upazila::bigint limit 1) current_upazila ,(select field_name from geo_data where id = current_union::bigint limit 1) current_union ,(select field_name from geo_data where id = current_ward::bigint limit 1) current_ward ,(select field_name from geo_data where id = permanent_division::bigint limit 1) permanent_division ,(select field_name from geo_data where id = permanent_district::bigint limit 1) permanent_district ,(select field_name from geo_data where id = permanent_upazila::bigint limit 1) permanent_upazila ,(select field_name from geo_data where id = permanent_union::bigint limit 1) permanent_union ,(select field_name from geo_data where id = permanent_ward::bigint limit 1) permanent_ward,substring(picture from 8) picture  FROM asf_victim where id = "+str(victim_tbl_id)
    df = pandas.read_sql(qry,connection)
    victim_id = df.victim_id.tolist()[0] if len(df.victim_id.tolist()) and df.victim_id.tolist()[0] is not None  else ''
    victim_name = df.victim_name.tolist()[0] if len(df.victim_name.tolist()) and df.victim_name.tolist()[0] is not None  else ''
    victim_sex = df.sex.tolist()[0] if len(df.sex.tolist()) and df.sex.tolist()[0] is not None  else ''
    birth_date = df.birth_date.tolist()[0] if len(df.birth_date.tolist()) and df.birth_date.tolist()[0] is not None  else ''
    victim_age = df.victim_age.tolist()[0] if len(df.victim_age.tolist()) and df.victim_age.tolist()[0] is not None  else ''
    mobile = df.mobile.tolist()[0] if len(df.mobile.tolist()) and df.mobile.tolist()[0] is not None  else ''
    mobile2 = df.mobile2.tolist()[0] if len(df.mobile2.tolist()) and df.mobile2.tolist()[0] is not None  else ''
    any_nid_brn_passport = df.any_nid_brn_passport.tolist()[0] if len(df.any_nid_brn_passport.tolist()) and df.any_nid_brn_passport.tolist()[0] is not None  else ''
    nid_brn_passport = df.nid_brn_passport.tolist()[0] if len(df.nid_brn_passport.tolist()) and df.nid_brn_passport.tolist()[0] is not None  else ''
    education = df.education.tolist()[0] if len(df.education.tolist()) and df.education.tolist()[0] is not None  else ''
    occupation = df.occupation.tolist()[0] if len(df.occupation.tolist()) and df.occupation.tolist()[0] is not None  else ''
    maritial_status = df.maritial_status.tolist()[0] if len(df.maritial_status.tolist()) and df.maritial_status.tolist()[0] is not None  else ''
    father_name = df.father_name.tolist()[0] if len(df.father_name.tolist()) and df.father_name.tolist()[0] is not None  else ''
    mother_name = df.mother_name.tolist()[0] if len(df.mother_name.tolist()) and df.mother_name.tolist()[0] is not None  else ''
    spouse_name = df.spouse_name.tolist()[0] if len(df.spouse_name.tolist()) and df.spouse_name.tolist()[0] is not None  else ''
    picture = df.picture.values[0][1] if len(df.picture.values) and df.picture.values[0][1] is not None  else ''
    current_division = df.current_division.values[0][1] if len(df.current_division.values) and df.current_division.values[0][1] is not None  else '%'
    current_district = df.current_district.values[0][1] if len(df.current_district.values) and df.current_district.values[0][1] is not None  else '%'
    current_upazila = df.current_upazila.values[0][1] if len(df.current_upazila.values) and df.current_upazila.values[0][1] is not None  else '%'
    current_union = df.current_union.values[0][1] if len(df.current_union.values) and df.current_union.values[0][1] is not None  else '%'
    current_ward = df.current_ward.values[0][1] if len(df.current_ward.values) and df.current_ward.values[0][1] is not None  else '%'
    current_address = df.current_address.tolist()[0] if len(df.current_address.tolist()) and df.current_address.tolist()[0] is not None  else ''
    current_postoffice = df.current_postoffice.tolist()[0] if len(df.current_postoffice.tolist()) and df.current_postoffice.tolist()[0] is not None  else ''
    present_permanent_address_same = df.present_permanent_address_same.tolist()[0] if len(df.present_permanent_address_same.tolist()) and df.present_permanent_address_same.tolist()[0] is not None  else ''
    permanent_division = df.permanent_division.values[0][1] if len(df.permanent_division.values) and df.permanent_division.values[0][1] is not None  else '%'
    permanent_district = df.permanent_district.values[0][1] if len(df.permanent_district.values) and df.permanent_district.values[0][1] is not None  else '%'
    permanent_upazila = df.permanent_upazila.values[0][1] if len(df.permanent_upazila.values) and df.permanent_upazila.values[0][1] is not None  else '%'
    permanent_union = df.permanent_union.values[0][1] if len(df.permanent_union.values) and df.permanent_union.values[0][1] is not None  else '%'
    permanent_ward = df.permanent_ward.values[0][1] if len(df.permanent_ward.values) and df.permanent_ward.values[0][1] is not None  else '%'
    permanent_address = df.permanent_address.tolist()[0] if len(df.permanent_address.tolist()) and df.permanent_address.tolist()[0] is not None  else ''
    permanent_postoffice = df.permanent_postoffice.tolist()[0] if len(df.permanent_postoffice.tolist()) and df.permanent_postoffice.tolist()[0] is not None  else ''
    injury_details = df.injury_details.tolist()[0] if len(df.injury_details.tolist()) and df.injury_details.tolist()[0] is not None  else ''
    notified_within_24h = df.notified_within_24h.tolist()[0] if len(df.notified_within_24h.tolist()) and df.notified_within_24h.tolist()[0] is not None  else ''
    verification_within_24h = df.verification_within_24h.tolist()[0] if len(df.verification_within_24h.tolist()) and df.verification_within_24h.tolist()[0] is not None  else ''
    brought_asf_within_48h = df.brought_asf_within_48h.tolist()[0] if len(df.brought_asf_within_48h.tolist()) and df.brought_asf_within_48h.tolist()[0] is not None  else ''

    user_id = request.user.id
    query = """ SELECT distinct '<div class="row"> <div class="col-lg-12"> <div class="panel-group"  role="tablist" aria-multiselectable="true"><div class="panel panel-default" style="margin-bottom: 10px;"><div style="height: 48px;" class="panel-heading" role="tab" id="heading'||category_id||'"><h4 class="panel-title"><a style="font-weight: bold;" class="collapsed"  onclick="load_forms('|| category_id ||',''internal_accordian'|| category_id ||''')" role="button" data-toggle="collapse"  href="#collapse'|| category_id ||'" aria-expanded="false" aria-controls="collapse'|| category_id ||'"> ' ||(SELECT category_name FROM forms_categories WHERE id = fc.category_id :: INT) || ' </a>'|| case when first_value(can_submit)over(PARTITION by category_id ORDER by can_submit desc) = 1 then '<a onclick="load_forms_list('|| category_id ||')"  class="btn btn-success btn-sm pull-right"   id="form'|| category_id ||'"  data-toggle="modal" data-target="#myModal"  ><i class="fa fa-4x fa fa-plus"></i></a>' else '' end  ||' </h4></div><div id="collapse'|| category_id ||'" class="panel-collapse collapse" role="tabpanel" aria-labelledby="heading'|| category_id ||'"><div class="panel-body"><div class="panel-group" id="internal_accordian'|| category_id ||'" role="tablist" aria-multiselectable="true"></div></div></div></div></div></div></div>' as form_str FROM vwrolewiseformpermission rf, forms_categories_relation fc WHERE ( rf.can_view = 1 OR rf.can_submit = 1) AND fc.form_id = rf.xform_id AND user_id = """ + str(user_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    main_str = ""
    for each in df['form_str']:
        main_str += str(each)
    main_str = json.dumps(main_str)
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    return render(request, "asfmodule/victim_profile.html",{
        'main_str': main_str,
        'username':username,
        'victim_tbl_id':victim_tbl_id,
        'victim_id':victim_id,
        'victim_name':victim_name,
        'victim_sex':victim_sex,
        'birth_date':birth_date,
        'victim_age':victim_age,
        'mobile':mobile,
        'mobile2':mobile2,
        'any_nid_brn_passport':any_nid_brn_passport,
        'nid_brn_passport':nid_brn_passport,
        'education':education,
        'occupation':occupation,
        'maritial_status':maritial_status,
        'father_name':father_name,
        'mother_name':mother_name,
        'spouse_name':spouse_name,
        'picture':picture,
        'current_division':current_division,
        'current_district':current_district,
        'current_upazila':current_upazila,
        'current_union':current_union,
        'current_ward':current_ward,
        'current_address':current_address,
        'current_postoffice':current_postoffice,
        'present_permanent_address_same':present_permanent_address_same,
        'permanent_division':permanent_division,
        'permanent_district':permanent_district,
        'permanent_upazila':permanent_upazila,
        'permanent_union':permanent_union,
        'permanent_ward':permanent_ward,
        'permanent_address':permanent_address,
        'permanent_postoffice':permanent_postoffice,
        'injury_details':injury_details,
        'notified_within_24h':notified_within_24h,
        'verification_within_24h':verification_within_24h,
        'brought_asf_within_48h':brought_asf_within_48h,
        'server_address':server_address
    })


@login_required
def victim_list(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/victim_list.html', {'divisions':divisions})

@csrf_exempt
def get_victims_list(request):
    division = request.POST.get('division')
    district = request.POST.get('district')
    status = request.POST.get('status')
    query = "select id,victim_id,(select incident_id from asf_case where id = case_id::int limit 1),victim_name ,(select incident_date from asf_case where id = case_id::int limit 1) ,mobile,sex,status,(select field_name from geo_data where id = current_division::int limit 1)division,(select field_name from geo_data where id = current_district::int limit 1) district ,(select field_name from geo_data where id = current_upazila::int limit 1) upazila ,(select field_name from geo_data where id = current_union::int limit 1) union_name ,current_address address from asf_victim where current_division like '"+str(division)+"' and current_district like '"+str(district)+"' and status like '"+str(status)+"'"
    # print(query)
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)

@login_required
def services_to_other_institutes_list(request):
    return render(request, 'asfmodule/services_to_other_institutes_list.html')

@csrf_exempt
def get_services_to_other_institutes_list(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = "WITH t AS(SELECT json ->> 'date' s_date, json ->> 'organization' organization, json ->> 'hospital' hospital, json ->> 'service' service, json ->> 'adult_female' adult_female, json ->> 'adult_male' adult_male, json ->> 'child_female' child_female, json ->> 'child_male' child_male, json ->> 'trangender' trangender, json ->> 'seasson_adult_female' seasson_adult_female, json ->> 'seasson_adult_male' seasson_adult_male, json ->> 'seasson_child_female' seasson_child_female, json ->> 'seasson_child_male' seasson_child_male, json ->> 'seasson_trangender' seasson_trangender, json ->> 'procedure' s_procedure FROM logger_instance WHERE xform_id = (SELECT id FROM logger_xform WHERE id_string = 'services_other_institute')) SELECT to_char(s_date::date,'DD/MM/YYYY') s_date, case when organization='1' then 'Govt Hospital' when organization='2' then 'E-Clinic' when organization='3' then 'Outreach' when organization='4' then 'Community Clinic' end organization, case when hospital='1' then 'SHNIBPS' when hospital='2' then 'DMCH' when hospital='3' then 'ShSMCH' when hospital='4' then 'SSMC' when hospital='5' then 'MMCH' when hospital='6' then 'KMCH' when hospital='7' then 'CMCH' when hospital='8' then 'CuMCH' when hospital='9' then 'VSC' else '' end hospital, case when service='1' then 'Physiotherapy' when service='2' then 'Psychotherapy' end service, adult_female, adult_male, child_female, child_male, trangender, seasson_adult_female, seasson_adult_male, seasson_child_female, seasson_child_male, seasson_trangender, coalesce(s_procedure,'') s_procedure FROM t  where s_date:: DATE between to_date('"+str(from_date)+"','DD/MM/YYYY') and to_date('"+str(to_date)+"','DD/MM/YYYY')"
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)

def services_to_other_institutes_form(request):
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='services_other_institute'")
    return render(request, 'asfmodule/services_to_other_institutes_form.html',{'username':username,'server_address':server_address,'form_id':form_id})


# Capacity Building
@login_required
def capacity_building_list(request):
    return render(request, 'asfmodule/capacity_building_list.html')

@csrf_exempt
def get_capacity_building_list(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = "with t as( select coalesce(json->>'event_name','') event_name, coalesce(json->>'event_type','') event_type, coalesce(json->>'training_type','') training_type, coalesce(json->>'capacity_building_subject','') capacity_building_subject, coalesce(json->>'capacity_building_subject_other','') capacity_building_subject_other, coalesce(json->>'event_start_date','') event_start_date, coalesce(json->>'event_end_date','') event_end_date, coalesce(json->>'division','') division, coalesce(json->>'district','') district, coalesce(json->>'union','') union_name, coalesce(json->>'ward','') ward, coalesce(json->>'participant_male','') participant_male, coalesce(json->>'participant_female','') participant_female, coalesce(json->>'participant_girl','') participant_girl, coalesce(json->>'participant_boy','') participant_boy, coalesce(json->>'participant_trangender','') participant_trangender, coalesce(json->>'particiapnt_total','') particiapnt_total, coalesce(json->>'organized_by','') organized_by, coalesce(json->>'organized_by_other','') organized_by_other, coalesce(json->>'funding_source','') funding_source,date_created s_date from logger_instance where xform_id = (select id from logger_xform where id_string='capacity_building')) select event_name, event_type, training_type, capacity_building_subject, capacity_building_subject_other, event_start_date, event_end_date, (select field_name from geo_data where id = division::int limit 1) division, (select field_name from geo_data where id = district::int limit 1) district, (select field_name from geo_data where id = union_name::int limit 1) union_name, (select field_name from geo_data where id = ward::int limit 1) ward, participant_male, participant_female, participant_girl, participant_boy, participant_trangender, particiapnt_total, organized_by, organized_by_other, funding_source from t where s_date:: DATE between to_date('"+str(from_date)+"','DD/MM/YYYY') and to_date('"+str(to_date)+"','DD/MM/YYYY')"
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)

def capacity_building_form(request):
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='capacity_building'")
    return render(request, 'asfmodule/capacity_building_form.html',{'username':username,'server_address':server_address,'form_id':form_id})

# Event
@login_required
def event_list(request):
    return render(request, 'asfmodule/event_list.html')

@csrf_exempt
def get_event_list(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = "with t as( select coalesce(json->>'event_type','') event_type, coalesce(json->>'event_name','') event_name, coalesce(json->>'organized_by','') organized_by, coalesce(json->>'funded_by','') funded_by, coalesce(json->>'venue','') venue, coalesce(json->>'event_start_date','') event_start_date, coalesce(json->>'event_end_date','') event_end_date, coalesce(json->>'event_duration','') event_duration, coalesce(json->>'participant_male','') participant_male, coalesce(json->>'participant_female','') participant_female, coalesce(json->>'participant_boy','') participant_boy, coalesce(json->>'participant_girl','') participant_girl, coalesce(json->>'participant_trangender','') participant_trangender, coalesce(json->>'participant_total','') participant_total, coalesce(json->>'participant_type','') participant_type, coalesce(json->>'achievement','') achievement, coalesce(json->>'remarks','') remarks, date_created s_date from logger_instance where xform_id = (select id from logger_xform where id_string='event')) select case when event_type = '1' then 'Training' when event_type = '2' then 'Workshop' when event_type = '3' then 'Conference' when event_type = '4' then 'Seminar'  end event_type, event_name, organized_by, funded_by, venue, event_start_date, event_end_date, event_duration, participant_male, participant_female, participant_boy, participant_girl, participant_trangender, participant_total, participant_type, achievement, remarks from t where s_date:: DATE between to_date('"+str(from_date)+"','DD/MM/YYYY') and to_date('"+str(to_date)+"','DD/MM/YYYY')"
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)

def event_form(request):
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='event'")
    return render(request, 'asfmodule/event_form.html',{'username':username,'server_address':server_address,'form_id':form_id})


# Paper clipping
@login_required
def paper_clipping_list(request):
    return render(request, 'asfmodule/paper_clipping_list.html')

@csrf_exempt
def get_paper_clipping_list(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = "with t as( select coalesce(json->>'newspaper_name','') newspaper_name, coalesce(json->>'news_publish_date','') news_publish_date, coalesce(json->>'newspaper_page_no','') newspaper_page_no, coalesce(json->>'category','') category, coalesce(json->>'remarks','') remarks, coalesce(json->>'news_scanned_file','') news_scanned_file, coalesce(json->>'news_publish_date','') s_date from logger_instance where xform_id = (select id from logger_xform where id_string='paper_clipping')) select newspaper_name, news_publish_date, newspaper_page_no, category, remarks, news_scanned_file from t where s_date:: DATE between to_date('"+str(from_date)+"','DD/MM/YYYY') and to_date('"+str(to_date)+"','DD/MM/YYYY')"
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)

def paper_clipping_form(request):
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='paper_clipping'")
    return render(request, 'asfmodule/event_form.html',{'username':username,'server_address':server_address,'form_id':form_id})