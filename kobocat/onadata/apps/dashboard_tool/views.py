import decimal
import simplejson
#from distutils.command.config import config
#from mercurial.dispatch import request

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Count, Q
from django.http import (HttpResponseRedirect, HttpResponse)
from django.shortcuts import render_to_response, get_object_or_404, render
from django.forms.formsets import formset_factory
from onadata.apps.dashboard_tool.forms import DashboardControlsGeneratorForm,DashboardNavigationBarForm
from django.db.models import ProtectedError
from django.db import connection
from django.db.models import Max, Sum
from onadata.apps.dashboard_tool.models import *
from onadata.apps.dashboard.models import *
import json
from datetime import *
from django.forms.models import inlineformset_factory
from collections import OrderedDict
from django.forms.formsets import BaseFormSet

from dateutil.relativedelta import relativedelta
from django.shortcuts import redirect




'''
*************************** Dynamic Dashboard TOOL *****************************************
'''


def index(request):
    return render(request, "dashboard_tool/index.html")



"""
Prepare json of given query for data table
@persia
"""

def getDatatable(query):
    data_list = []
    col_names = []
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchall();
    col_names = [i[0] for i in cursor.description]
    col_names.append('Action')
    for eachval in fetchVal:
        delete_button = '<a class="delete-program-item tooltips" data-placement="top" href="#" data-original-title="Delete"  onclick="delete_entity('+ str(eachval[0]) +')"><i class="fa fa-2x fa-trash-o"></i></a>'
        #delete_button = ''
        edit_button = '<a class="tooltips" data-placement="top" data-original-title="Edit Program" href="#" onclick="edit_entity(' + str(
            eachval[0]) + ');"><i class="fa fa-2x fa-pencil-square-o"></i></a>' + ' ' + delete_button
        eachval = eachval + (edit_button,)
        data_list.append(list(eachval))
    return json.dumps({'col_name': col_names, 'data': data_list})


"""
Prepare Message for Ajax request message
@persia
"""
def getAjaxMessage(type, message):
    data = {}
    data['type'] = type
    data['messages'] = message
    return data



'''
***************UTILITY functions for running raw queries***************
'''
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


def dictfetchall(cursor):
    desc = cursor.description
    return [
        OrderedDict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()]


def run_query(query):
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    cursor.close()




'''
****************CALLING FUNCTION of GENERATORS******************
'''

def build_dashboard_index(request):
    navigationBar = DashboardNavigationBar.objects.all()
    chart_types=DashboardChartType.objects.all()
    #Set initial colors of graph
    colors = ['#058DC7', '#50B432', '#ED561B', '#DDDF00', '#24CBE5', '#64E572', '#FF9655', '#FFF263', '#6AF9C4']
    context = {
        "navigationBar":navigationBar,
        "colors": colors,
        "chart_types":chart_types
    }
    return render(request, 'dashboard_tool/build_dashboard.html', context)


def generate_chart(request):
    jsondataList=[]
    jsondata={}
    jsondata["name"]="col1"
    jsondata["y"] = 0
    jsondataList.append(jsondata.copy())
    return HttpResponse(json.dumps([{"y": 6, "name": 'First'},{"y": 7, "name": 'Second'}, {"y": 9, "name": 'Third'},{"y": 1, "name": 'Fourth'},{"y": 1, "name": 'Fifth'}]), content_type="application/json")




##*********************Json Serialize (Start)****************
'''
@author:Emtious
'''
def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj

'''
@author:Emtious
'''
def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError

'''
@author:Emtious
'''
def getUniqueValues(dataset, colname):
    list = [];

    for dis in dataset:
        if dis[colname] in list:
            continue;
        else:
            list.append(dis[colname]);
    return list;


'''
@author:Emtious
'''
def generate_json_bar_line_area_Chart(category_field,data_field, query):

    dataset = __db_fetch_values_dict(query);
    category_list = getUniqueValues(dataset, category_field)
    seriesData = []
    dict = {}
    dict['data'] = [nameTodata[data_field] for nameTodata in dataset  ]
    seriesData.append(dict)
    jsonForChart = json.dumps({'categories': category_list, 'seriesdata': seriesData}, default=decimal_default)
    return jsonForChart



'''
Percentage Area Chart
Multiple Area chart
'''
def generate_json_column_area_chart(name_field, category_field,data_field, query):
    dataset = __db_fetch_values_dict(query)  ## ******  ( Category for multiple value of each Legend) ******* (Start)    '''
    print dataset
    uniqueList = getUniqueValues(dataset, name_field)
    category_list = getUniqueValues(dataset, category_field)
    seriesData = []
    for ul in uniqueList:
        print(ul)
        dict = {}
        dict['name'] = ul;
        dict['data'] = [nameTodata[data_field] for nameTodata in dataset if nameTodata[name_field] == ul]
        seriesData.append(dict)
    jsonForChart = json.dumps({'categories': category_list, 'seriesdata': seriesData}, default=decimal_default)
    return jsonForChart



def get_member_chart(request):
    query = "SELECT  (select name from geo_ward where id=geo_ward_id) as category, sum(hh_member_number) as value FROM public.household group by geo_ward_id";

    jsondata = generate_json_column_area_chart('name','category', 'value', query)
    #jsondata= generate_json_bar_line_area_Chart( 'category','value' , query)
    print jsondata
    return HttpResponse(jsondata,content_type="application/json")





'''
****************TOOL: Graph Generator *************
'''
def get_graph_json(request):
    chart_type=request.POST.get("chart_type")
    query=request.POST.get("query")
    return HttpResponse( execute_query(chart_type,query), content_type="application/json")


def get_generated_graph(request):
    context={"html_code": request.POST.get("html_code"),
    "js_code": request.POST.get("js_code") }
    return render(request, "dashboard_tool/get_generated_graph.html",context)

#DASHBOARD_APP @DUPLICATE
def execute_query(chart_type, query):
    #TODO Add more Chart type and check before excuting
    jsondata=''
    if chart_type==1:
        jsondata = generate_json_column_area_chart('name', 'category', 'value', query)
    else:
        jsondata = generate_json_bar_line_area_Chart('category', 'value', query)
    return jsondata;


#DASHBOARD_APP @DUPLICATE
def get_filtered_query(post_dict, query):
    keyward_param=""
    for key in post_dict:
        keyward_param="@"+key
        if keyward_param in query:
            query=query.replace(keyward_param, post_dict[key])

    return query;


def save_dashboard_style(request):
    #slaMeeting_form = SlaMeetingForm(instance=hh_sla)
    if request.method == 'POST':
        print "Test    ", request.POST.get("chart_type")
        dashboardGenerator=DashboardGenerator()
        dashboardGenerator.html_code =  request.POST.get("html_code")
        if (request.POST.get("chart_type") is not None) and (request.POST.get("chart_type") !='' ) :
            dashboardGenerator.chart_type_id =int(request.POST.get("chart_type"))
        dashboardGenerator.content_type = request.POST.get("content_type")
        dashboardGenerator.content_order = request.POST.get("content_order")
        dashboardGenerator.chart_object = request.POST.get("chart_object")
        dashboardGenerator.js_code = request.POST.get("js_code")
        dashboardGenerator.filtering = "{}"
        dashboardGenerator.element_id =  request.POST.get("element_id")
        dashboardGenerator.navigation_bar_id = int(request.POST.get("tab_no"))
        dashboardGenerator.datasource_type = request.POST.get("datasource_type")
        dashboardGenerator.datasource = request.POST.get("datasource")
        dashboardGenerator.save()
        dashboardGenerator.post_url = "/dashboard/generate_graph/" + str(dashboardGenerator.id) + "/"
        dashboardGenerator.save()
        return HttpResponse("Hello", status=200)
    else:
        return HttpResponse("Hello", status=500)


def generate_graph(request, graph_id):
    dashboardGenerator = DashboardGenerator.objects.filter(id=graph_id).first()
    jsondata={}

    if dashboardGenerator.datasource_type=="1":
        query=get_filtered_query(request.POST, dashboardGenerator.datasource)
        jsondata = execute_query("chart_type",query)
    else:
        #TODO: URL will Return a json
        jsondata = HttpResponseRedirect(dashboardGenerator.datasource)
    return HttpResponse(jsondata, content_type="application/json")



def show_graph_list(request):
    return render(request,"dashboard_tool/show_graph_list.html");



def show_graph_def_get_json(request):
    datajson = getDatatable('select id, (select link_name from dashboard_navigation_bar where id=navigation_bar_id ) as Tab, datasource as Datasource, chart_object from dashboard_generator')
    return HttpResponse(datajson, content_type='application/json')



def delete_graph_def(request, graph_id):
    graph_def_instance = DashboardGenerator.objects.get(pk=graph_id)
    try:
        graph_def_name=graph_def_instance.id;
        graph_def_instance.delete()
        data=getAjaxMessage("success",'<i class="fa fa-check-circle"></i> graph_def -'+str(graph_def_name)+' has been deleted successfully!')
    except ProtectedError:
        graph_def_del_message = "graph_def could not be deleted."
        data=getAjaxMessage("danger", graph_def_del_message)
    return HttpResponse(simplejson.dumps(data), content_type="application/json")





'''
***************************** Navigation Bar Tool**************************************
'''

def add_navigation_bar(request):
    navigation_form = DashboardNavigationBarForm()
    #navigationBar = DashboardNavigationBar.objects.filter(parent_link_id__isnull=True)
    context = {
        #"navigationBar": navigationBar,
        "navigation_form":navigation_form
    }
    if request.method=="POST":
        navigation_form = DashboardNavigationBarForm(data=request.POST)
        if navigation_form.is_valid():
            navigation_form_instance = navigation_form.save()
            navigation_form = DashboardNavigationBarForm()
            context = {
                "navigation_form": navigation_form
            }
            return render(request, "dashboard_tool/add_navigation_bar_form.html", context)
        else:
            return render(request, "dashboard_tool/add_navigation_bar_form.html", context)
    return render(request, "dashboard_tool/add_navigation_bar.html", context)


def show_navigation_bar(request):
    datajson=getDatatable('select * from dashboard_navigation_bar')
    return HttpResponse(datajson, content_type='application/json')



 
def edit_navigation_bar(request, navigation_bar_id):
    NAVIGATION_EDIT_ID = navigation_bar_id
    if request.method == 'GET':
        navigation_form_instance = DashboardNavigationBar.objects.filter(id=navigation_bar_id).first()
        navigation_form = DashboardNavigationBarForm(instance=navigation_form_instance)

    elif request.method == 'POST':
        navigation_form_instance = DashboardNavigationBar.objects.filter(id=navigation_bar_id).first()
        navigation_form = DashboardNavigationBarForm(data=request.POST,instance=navigation_form_instance)
        context = {
            "navigation_form": navigation_form
        }
        if navigation_form.is_valid():
            navigation_form_instance=navigation_form.save()
            #navigation_form = DashboardNavigationBarForm()
            return render(request, "dashboard_tool/add_navigation_bar_form.html", context);
        else:
            # Form is not valid, Send Error message with Form
            return render(request, "dashboard_tool/add_navigation_bar_form.html", context);
    else:
        navigation_form = DashboardNavigationBarForm()

    return render(request,'dashboard_tool/add_navigation_bar_form.html',{'navigation_form': navigation_form, 'NAVIGATION_EDIT_ID': NAVIGATION_EDIT_ID})



def delete_navigation_bar(request, navigation_bar_id):
    navigation_bar_instance = DashboardNavigationBar.objects.get(pk=navigation_bar_id)
    try:
        navigation_bar_name=navigation_bar_instance.link_name;
        navigation_bar_instance.delete()
        data=getAjaxMessage("success",'<i class="fa fa-check-circle"></i> navigation_bar -'+navigation_bar_name+' has been deleted successfully!')
    except ProtectedError:
        navigation_bar_del_message = "navigation_bar could not be deleted."
        data=getAjaxMessage("danger", navigation_bar_del_message)
    return HttpResponse(simplejson.dumps(data), content_type="application/json")


'''
***************************** Filtering Control Section**************************************
'''

def add_filtering_control(request):
    filtering_form = DashboardControlsGeneratorForm()
    context = {
        "filtering_form": filtering_form
    }
    if request.method=="POST":
        filtering_form = DashboardControlsGeneratorForm(data=request.POST)
        if filtering_form.is_valid():
            filtering_control_instance = filtering_form.save()
            filtering_control_instance.control_id = filtering_control_instance.control_name + "_" + str(filtering_control_instance.id)
            filtering_control_instance.save()
            context = {
                "filtering_form": filtering_form
            }
            return render(request, "dashboard_tool/add_filtering_control_form.html", context);
        else:
            return render(request, "dashboard_tool/add_filtering_control_form.html", context, status=500);
    return render(request,"dashboard_tool/add_filtering_control.html",context);


def edit_filtering_control(request, control_id):
    CONTROL_EDIT_ID=control_id
    if request.method=="GET":
        filtering_form_instance = DashboardControlsGenerator.objects.filter(id=control_id).first()
        filtering_form = DashboardControlsGeneratorForm(instance=filtering_form_instance)
        context = {
            "filtering_form": filtering_form,
            "CONTROL_EDIT_ID":CONTROL_EDIT_ID
        }
    if request.method=="POST":
        filtering_form_instance = DashboardControlsGenerator.objects.filter(id=control_id).first()
        filtering_form = DashboardControlsGeneratorForm(data=request.POST, instance=filtering_form_instance)
        if filtering_form.is_valid():
            filtering_control_instance = filtering_form.save()
            filtering_control_instance.control_id = filtering_control_instance.control_name+"_" + str(filtering_control_instance.id)
            print filtering_control_instance.control_id
            filtering_control_instance.save()
            context = {
                "filtering_form": filtering_form,
                "CONTROL_EDIT_ID":CONTROL_EDIT_ID
            }
            return render(request, "dashboard_tool/add_filtering_control_form.html", context);
        else:
            return render(request, "dashboard_tool/add_filtering_control_form.html", context, status=500);
    return render(request,"dashboard_tool/add_filtering_control.html",context);




def show_filtering_control(request):
    return render(request,"dashboard_tool/show_filtering_control.html");



def show_filtering_control_get_json(request):
    datajson = getDatatable('select id, control_label as Label, control_type as Type, datasource as Datasource from dashboard_controls_generator')
    return HttpResponse(datajson, content_type='application/json')




def delete_filtering_control(request, control_id):
    filtering_control_instance = DashboardControlsGenerator.objects.get(pk=control_id)
    try:
        filtering_control_name=filtering_control_instance.control_label;
        filtering_control_instance.delete()
        data=getAjaxMessage("success",'<i class="fa fa-check-circle"></i> filtering_control -'+filtering_control_name+' has been deleted successfully!')
    except ProtectedError:
        filtering_control_del_message = "filtering_control could not be deleted."
        data=getAjaxMessage("danger", filtering_control_del_message)
    return HttpResponse(simplejson.dumps(data), content_type="application/json")



