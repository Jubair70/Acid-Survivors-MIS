from django.http import (
    HttpResponseRedirect, HttpResponse)
from django.shortcuts import render_to_response,render,get_object_or_404
from django.template import RequestContext,loader
#from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
import json
import sys
# Unicef Imports
from onadata.apps.logger.models import Instance, XForm
from onadata.apps.unicef.models import GeoTable, GeoRMO, GeoPSU
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.db import connection
# form imports
from onadata.apps.unicef.forms import GeoForm, GeoRMOForm, GeoPSUForm
from onadata.apps.usermodule.views_project import get_viewable_projects
from onadata.settings import unicef_config
# ======================== Unicef Part ==============================

@login_required
def geo_index(request):
    context = RequestContext(request)
    all_geo = GeoTable.objects.all()
    # "message":message,"alert":alert,'org_del_message':org_del_message
    return render_to_response(
            'unicef/geo_list.html',
            {'all_geo':all_geo},
            context)

@login_required
def add_geodata(request):
    context = RequestContext(request)
    # all_menu = MenuItem.objects.all()
    # A boolean value for telling the template whether
    # the registration was successful.
    # Set to False initially. Code changes value to True
    # when registration succeeds.
    is_added = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        geo_form = GeoForm(data=request.POST)
        # If the two forms are valid...
        if geo_form.is_valid():
            geo_form.save()
            # menu.save()
            is_added = True
        else:
            print geo_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
        return HttpResponseRedirect('/unicef/geodata/')
    else:
        geo_form = GeoForm()
    # Render the template depending on the context.
        return render_to_response(
            'unicef/add_geodata.html',
            {'geo_form': geo_form, # 'all_menu':all_menu,
            'is_added': is_added},
            context)


@login_required
def edit_geodata(request, geo_id):
    context = RequestContext(request)
    edited = False
    geo_item = GeoTable.objects.get(pk=geo_id)
    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        geo_form = GeoForm(data=request.POST, instance=geo_item)
        # If the two forms are valid...
        if geo_form.is_valid():
            geo_form.save()
            edited = True
        else:
            print geo_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        geo_form = GeoForm(instance=geo_item)

    return render_to_response(
            'unicef/edit_geoitem.html',
            {'id':geo_id, 'geo_form': geo_form,
            'edited': edited},
            context)


@login_required
def delete_geodata(request, geo_id):
    context = RequestContext(request)
    geoitem = GeoTable.objects.get(pk=geo_id)
    # deletes the user from both user and rango
    geoitem.delete()
    return HttpResponseRedirect('/unicef/geodata')


@login_required
def rmo_index(request):
    context = RequestContext(request)
    all_geo = GeoRMO.objects.all()
    # "message":message,"alert":alert,'org_del_message':org_del_message
    return render_to_response(
            'unicef/geo_rmo_list.html',
            {'all_geo':all_geo},
            context)

@login_required
def add_geo_rmo(request):
    context = RequestContext(request)
    # all_menu = MenuItem.objects.all()
    # A boolean value for telling the template whether the
    # registration was successful.
    # Set to False initially. Code changes value to True when
    # registration succeeds.
    is_added = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        geo_rmo_form = GeoRMOForm(data=request.POST)
        # If the two forms are valid...
        if geo_rmo_form.is_valid():
            # geo_rmo_form.save();
            v_rmo_id = request.POST['rmo_id']
            v_rmo_type = request.POST['rmo_type']
            try:
                GeoRMO(rmo_id=v_rmo_id, rmo_type=v_rmo_type).save()
            except IntegrityError:
                return HttpResponseRedirect('/unicef/geo-rmo-list/?error=exists')
            is_added = True
            return HttpResponseRedirect('/unicef/geo-rmo-list/')
        else:
            # print geo_rmo_form.errors
            return render_to_response(
            'unicef/add_rmo.html',
            {'geo_rmo_form': geo_rmo_form,
            'is_added': is_added},
            context)

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        geo_rmo_form = GeoRMOForm()
    # Render the template depending on the context.
        return render_to_response(
            'unicef/add_rmo.html',
            {'geo_rmo_form': geo_rmo_form,
            'is_added': is_added},
            context)


@login_required
def edit_geo_rmo(request, rmo_id):
    context = RequestContext(request)
    edited = False
    geo_item = GeoRMO.objects.get(pk = rmo_id)
    
    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        geo_rmo_form = GeoRMOForm(data=request.POST)
        # If the two forms are valid...
        if geo_rmo_form.is_valid():
            v_rmo_id = request.POST['rmo_id']
            v_rmo_type = request.POST['rmo_type']
            try:
                geo_item.rmo_id = v_rmo_id
                geo_item.rmo_type = v_rmo_type
                geo_item.save()
                
            except IntegrityError:
                return HttpResponseRedirect('/unicef/geo-rmo-list/?error=exists')
            
            edited = True
        else:
            print geo_rmo_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        geo_rmo_form = GeoRMOForm(initial={'rmo_id': geo_item.rmo_id,'rmo_type': geo_item.rmo_type})

    return render_to_response(
            'unicef/edit_geo_rmo.html',
            {'id':rmo_id, 'geo_rmo_form': geo_rmo_form,
            'edited': edited},
            context)


@login_required
def delete_geo_rmo(request,rmo_id):
    context = RequestContext(request)
    geoitem = GeoRMO.objects.get(pk = rmo_id)
    # deletes the user from both user and rango
    geoitem.delete()
    return HttpResponseRedirect('/unicef/geo-rmo-list')


@login_required
def psu_index(request):
    context = RequestContext(request)
    all_geo = GeoPSU.objects.all()
    message = request.GET.get('message')
    # "message":message,"alert":alert,'org_del_message':org_del_message
    return render_to_response(
            'unicef/geo_psu_list.html',
            {'all_geo':all_geo,'message':message},
            context)

@login_required
def add_geo_psu(request):
    context = RequestContext(request)
    # all_menu = MenuItem.objects.all()
    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    is_added = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        geo_psu_form = GeoPSUForm(data=request.POST)
        # If the two forms are valid...
        if geo_psu_form.is_valid():
            v_psu_id = request.POST['psu_id']
            v_name = request.POST['name']
            v_geo_division = GeoTable.objects.get(pk=request.POST['geo_division'])
            v_geo_district = GeoTable.objects.get(pk=request.POST['geo_district'])
            v_geo_upazilla = GeoTable.objects.get(pk=request.POST['geo_upazilla'])
            v_geo_union = GeoTable.objects.get(pk=request.POST['geo_union'])
            v_geo_rmo = GeoRMO.objects.get(pk=request.POST['geo_rmo'])
            GeoPSU(psu_id=v_psu_id, name=v_name, geo_division=v_geo_division, geo_district=v_geo_district, geo_upazilla=v_geo_upazilla ,geo_rmo=v_geo_rmo,geo_union=v_geo_union).save()
            # geo_psu_form.save();
            is_added = True
            return HttpResponseRedirect('/unicef/geo-psu-list/')
        else:
            # print geo_rmo_form.errors
            return render_to_response(
            'unicef/add_psu.html',
            {'geo_psu_form': geo_psu_form,
            'is_added': is_added},
            context)

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        geo_psu_form = GeoPSUForm()
    
    # Render the template depending on the context.
        return render_to_response(
            'unicef/add_psu.html',
            {'geo_psu_form': geo_psu_form,
            'is_added': is_added},
            context)


@login_required
def edit_geo_psu(request, psu_id):
    context = RequestContext(request)
    edited = False
    geo_item = GeoPSU.objects.get(pk=psu_id)
    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        geo_psu_form = GeoPSUForm(data=request.POST,geo_item=geo_item)
        # If the two forms are valid...
        if geo_psu_form.is_valid():
            geo_item.psu_id = request.POST['psu_id']
            geo_item.name = request.POST['name']
            geo_item.geo_division = GeoTable.objects.get(pk=request.POST['geo_division'])
            geo_item.geo_district = GeoTable.objects.get(pk=request.POST['geo_district'])
            geo_item.geo_upazilla = GeoTable.objects.get(pk=request.POST['geo_upazilla'])
            geo_item.geo_union = GeoTable.objects.get(pk=request.POST['geo_union'])
            geo_item.geo_rmo = GeoRMO.objects.get(pk=request.POST['geo_rmo'])
            geo_item.save()
            edited = True
        else:
            print geo_psu_form.errors
            render_to_response(
                'unicef/edit_geo_psu.html',
                {'id':psu_id, 'geo_psu_form': geo_psu_form,
                'edited': edited},
                context)
    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        geo_psu_form = GeoPSUForm(geo_item=geo_item)
    return render_to_response(
            'unicef/edit_geo_psu.html',
            {'id':psu_id, 'geo_psu_form': geo_psu_form,
            'edited': edited},
            context)

    '''
def delete_organization(request,org_id):
    context = RequestContext(request)
    org = Organizations.objects.get(pk = org_id)
    try:
        org.delete()
    except ProtectedError:
        org_del_message = """User(s) are assigned to this organization,
        please delete those users or assign them a different organization
        before deleting this organization"""
        return HttpResponseRedirect('/usermodule/organizations/?org_del_message='+org_del_message)
    return HttpResponseRedirect('/usermodule/organizations/')

    '''

@login_required
def delete_geo_psu(request,psu_id):
    context = RequestContext(request)
    geoitem = GeoPSU.objects.get(pk = psu_id)
    try:
        geoitem.delete()
    except ProtectedError:
        del_message = """User(s) are assigned to this PSU,
        please delete those users or assign them a different PSU
        before deleting this PSU"""
        return HttpResponseRedirect('/unicef/geo-psu-list/?message='+del_message)
    return HttpResponseRedirect('/unicef/geo-psu-list')


@login_required
def get_children(request):
    param_user_id = request.POST['id']
    response_data = {}
    geodata = GeoTable.objects.filter(parent__pk=param_user_id)
    response_data = []
    for geo_item in geodata:
        data = {}
        data["id"] = geo_item.pk
        data["name"] = geo_item.name
        response_data.append(data) 
    
    return HttpResponse(json.dumps(response_data), content_type="application/json")


@login_required
def data_view_project(request):
    context = RequestContext(request)
    user = request.user
    forms_id = []
    xforms_list = get_viewable_projects(request)
    for x in xforms_list:
        forms_id.append(x.id)
    count = 0
    data_list = []
    for f_id in forms_id:
        data = Instance.objects.filter(xform_id = f_id)
        form_data = XForm.objects.get(id = f_id)
        
        
        form_creator = form_data.user.username
        for d in data:
            x = json.dumps(d.json)
            data_list.append(has_form_username(form_creator,count,d.pk,x))
            count = count + 1
    # deletes the user from both user and rango
    return render_to_response(
            'unicef/data_table.html',
            {'user':user,'data':data_list },
            context)


class HTMLDataFormat(object):
    def __init__(self,serial,form_name,household_id,member_name,submitted_by,date,url):
        self.serial = serial
        self.form_name = form_name
        self.household_id = household_id
        self.member_name = member_name
        self.submitted_by = submitted_by
        self.date = date
        self.url = url


def has_form_username(form_creator,count,id,xjson):
    data = json.loads(xjson)
    url = '/'+form_creator+'/forms/'+data['_xform_id_string']+'/instance#/'+str(id)
    if 'username' not in data:
        data['username'] = "N/A"
    # html_object = HTMLDataFormat(count,data['_xform_id_string'],data['Household_ID_'],data['Member_Name_'],data['username'],data['_submission_time'],url)
    html_object = HTMLDataFormat(count,data['_xform_id_string'],"","",data['username'],data['_submission_time'],url)
    return html_object        


@login_required
def dynamic_ajax(request):
    param_user_id = request.POST['id']
    response_data = {}
    geodata = GeoPSU.objects.all()
    response_data = []
    # headers of table
    data = {}
    data["id"] = "ID"
    data["name"] = "Name"
    response_data.append(data)
    for geo_item in geodata:
        data = {}
        data["id"] = geo_item.pk
        data["name"] = geo_item.name
        response_data.append(data)
    
    return HttpResponse(json.dumps(response_data), content_type="application/json")

@require_GET
@login_required
def get_options(request):
    response_data = []
    username = request.user
    query =request.GET['q'].split("_") 
    if(query[0] == 'initial'):
        geoData = GeoTable.objects.filter(geo_type='DC')
    if(query[0] =='UP'):
        geoData = GeoTable.objects.filter(geo_type='UP', parent_id=int(query[1]))
    if(query[0] =='UN'):
        geoData = GeoTable.objects.filter(geo_type='UN', parent_id=int(query[1]))
    if(query[0] =='PSU'):
        geoData = GeoPSU.objects.filter(geo_union=int(query[1]))

    for geo_item in geoData:
        data = {}
        data["id"] = geo_item.pk
        data["name"] = geo_item.name
        response_data.append(data)
    #print 'geodata'+ str(response_data)    


    
    return HttpResponse(json.dumps(response_data), content_type="application/json")

@login_required
def create_dashboard(request):
    reportData = {}
    username = request.user
    
    xform_birth = get_object_or_404(XForm,id=unicef_config.xFORM_BIRTH_ID)
    xform_feeding = get_object_or_404(XForm,id=unicef_config.xFORM_FEEDING_ID)
    xform_diet = get_object_or_404(XForm,id=unicef_config.xFORM_DIET_ID)
    xform_household = get_object_or_404(XForm,id=unicef_config.xFORM_HOUSEHOLD_ID)
    reportData[str(xform_birth.id_string)] = str(xform_birth.title)
    reportData[str(xform_feeding.id_string)] = str(xform_feeding.title) 
    reportData[str(xform_diet.id_string)] = str(xform_diet.title) 
    reportData[str(xform_household.id_string)] = str(xform_household.title)
    

    variables = RequestContext(request, {
        'head_title': 'Project Summary',
        'reportdata':json.dumps(reportData),
        'jasper_url': unicef_config.JASPER_SERVER_URL,
        'jasper_rprt_exec_url':unicef_config.JASPER_REPORT_EXECUTION_URL,
        'jasper_param_query':unicef_config.JASPER_REPORT_PARAMETER_QUERY,
        })
    output = render(request,'unicef/unicef_dashboard.html',variables);
    return HttpResponse(output);

@login_required
def create_br_report(request):
    reportData = {}
    param = 0
    username = request.user
    district_param = "%"
    upazilla_param = "%"
    union_param = "%"
    psu_param = "%"
    from_date_param = "%"
    to_date_param = "%"
    if request.is_ajax():
        district_param = request.POST.get('district',0)
        upazilla_param = request.POST.get('upazilla',0)
        union_param = request.POST.get('union',0)
        psu_param = request.POST.get('psu',0)
        from_date_param = request.POST.get('from_date','')
        to_date_param = request.POST.get('to_date','')

    xform_birth = get_object_or_404(XForm,id=unicef_config.xFORM_BIRTH_ID)
    xform_feeding = get_object_or_404(XForm,id=unicef_config.xFORM_FEEDING_ID)
    xform_diet = get_object_or_404(XForm,id=unicef_config.xFORM_DIET_ID)
    xform_household = get_object_or_404(XForm,id=unicef_config.xFORM_HOUSEHOLD_ID)
    
    reportData[str(xform_birth.id_string)] = str(xform_birth.title)
    reportData[str(xform_feeding.id_string)] = str(xform_feeding.title) 
    reportData[str(xform_diet.id_string)] = str(xform_diet.title) 
    reportData[str(xform_household.id_string)] = str(xform_household.title)

    #birth registration queries:
    results = []
    c = connection.cursor()
    try:
        c.execute("BEGIN")
        c.callproc("show_tanahasi_data",(str(district_param),str(upazilla_param),str(union_param),str(psu_param),7))
        results = c.fetchone()
        c.execute("COMMIT")
    finally:
        c.close()
        for item in results:
            reportData[str('Accessibility')] = str(item['accessability'])
            reportData[str('Utilization')] = str(item['utilization'])
            reportData[str('Adequate_Coverage')] = str(item['adequate'])
            reportData[str('Effective_Coverage')] = str(item['effective'])

            reportData[str('Have_Birth_Certificate')] = str(item['has_bc'])
            reportData[str('Seen_Birth_Certificate')] = str(item['see_bc'])
            reportData[str('Registered_within_45_days')] = str(item['reg_bf_45'])

            reportData[str('Know_where_apply')] = str(item['know_where_apply'])
            reportData[str('Know_how_application')] = str(item['know_how_apply'])
            reportData[str('Know_who_help')] = str(item['know_who_help'])
    variables = RequestContext(request, {
        'head_title': 'Birth Registration Report',
        'reportdata':json.dumps(reportData),
        })

    if request.is_ajax():
        output = json.dumps(reportData)
        return HttpResponse(output,content_type='application/json');   
    else:
        output = render(request,'unicef/unicef_br_report.html',variables);
        return HttpResponse(output);   


def getCount(execution_query):
    cursor = connection.cursor()
    cursor.execute(execution_query)
    fetchVal = cursor.fetchone();
    return fetchVal[0]

