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
    print(query)
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
    current_user = UserModuleProfile.objects.get(user_id=request.user.id)
    role = UserRoleMap.objects.get(user=current_user.pk)
    role_id = role.role.pk
    query = """ WITH t AS(SELECT (SELECT title FROM logger_xform WHERE id = form_id), form_id FROM rolewiseform rf, forms_categories_relation fc WHERE ( rf.can_view = 1 OR rf.can_submit = 1) AND category_id = """ +str(category_id)+ """ AND fc.form_id = rf.xform_id AND role_id = """+str(role_id)+""") ,t1 as (select logger_instance.id log_ins_id,json::text adolescent_name,* FROM t,logger_instance where t.form_id = logger_instance.xform_id) select '<div class="panel panel-default" ><div class="panel-heading" role="tab" id="heading'||log_ins_id ||'"><h4 class="panel-title"><a  onclick="load_forms_data('||log_ins_id ||',''data_view'|| log_ins_id ||''')" role="button" data-toggle="collapse" href="#collapse'|| log_ins_id ||'" aria-expanded="false" aria-controls="collapse'||log_ins_id ||'">'|| date_created::date ||' '||title|| '</a></h4></div><div id="collapse'|| log_ins_id ||'" class="panel-collapse collapse" role="tabpanel" aria-labelledby="heading'|| log_ins_id ||'"><div class="panel-body"><div class="ribbon" id="data_view'|| log_ins_id ||'"></div></div></div></div>' as form_str from t1 where adolescent_name like '%""" + str(victim_id) + """%' """
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
    category_id = request.GET.get('category_id')
    victim_id = request.GET.get('victim_id')
    current_user = UserModuleProfile.objects.get(user_id=request.user.id)
    role = UserRoleMap.objects.get(user=current_user.pk)
    role_id = role.role.pk
    query = """ WITH t AS(SELECT (SELECT title FROM logger_xform WHERE id = form_id), form_id FROM rolewiseform rf, forms_categories_relation fc WHERE ( rf.can_submit = 1) AND category_id = """ +str(category_id)+ """ AND fc.form_id = rf.xform_id AND role_id = """+str(role_id)+""") ,t1 as (select logger_instance.id log_ins_id,json::text adolescent_name,* FROM t,logger_instance where t.form_id = logger_instance.xform_id) select distinct '<a  ng-click="load_forms_html('|| form_id ||')" href="#" >'|| title ||'</a>' as popup_str from t1 where adolescent_name like '%""" + str(victim_id) + """%' """
    print(query)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    main_str = """ <ul class="list-group"> """
    for each in df['popup_str']:
        main_str += """ <li class="list-group-item"> """ + str(each) + """ </li> """
    main_str += """ </ul> """
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


