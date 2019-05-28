import decimal
import simplejson
# from distutils.command.config import config
# from mercurial.dispatch import request

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Count, Q
from django.http import (HttpResponseRedirect, HttpResponse)
from django.shortcuts import render_to_response, get_object_or_404, render
from onadata.apps.dashboard.forms import *
from django.db.models import ProtectedError
from django.db import connection
from django.db.models import Max, Sum
from onadata.apps.dashboard.models import *
import json
import re
from datetime import *
from django.forms.models import inlineformset_factory
from collections import OrderedDict
from django.forms.formsets import BaseFormSet

from dateutil.relativedelta import relativedelta
from django.shortcuts import redirect

from django.views.decorators.csrf import csrf_exempt
from onadata.apps.dashboard import utility_functions
from django.conf import settings
from django.http import HttpResponse
import pandas as pd
import xlwt
from random import randint
import os
from onadata.apps.usermodule.models import UserModuleProfile

# *************************** Household (hh) Module *****************************************



'''
Lis of Constants for sla meeting
@persia
'''
DS_QUERY = '1'
DS_URL = '2'
DS_STATIC_JSON = '3'
DS_NOT_APPLICABLE = '4'

"""
Prepare json of given query for data table
@persia
"""


def index(request):
    return render(request, "dashboard/index.html")


def getDashboardDatatable(query):
    data_list = []
    col_names = []
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchall();
    col_names = [i[0] for i in cursor.description]
    # col_names.append('Action')
    for eachval in fetchVal:
        # delete_button = '<a class="delete-program-item tooltips" data-placement="top" href="#" data-original-title="Delete Program"  onclick="delete_program('+ str(eachval[0]) +')"><i class="fa fa-2x fa-trash-o"></i></a>'
        delete_button = ''
        edit_button = '<a class="tooltips" data-placement="top" data-original-title="Edit Program" href="#" onclick="edit_entity(' + str(
            eachval[0]) + ');"><i class="fa fa-2x fa-pencil-square-o"></i></a>' + ' '
        # eachval = eachval + (edit_button,)
        data_list.append(list(eachval))
    return json.dumps({'col_name': col_names, 'data': data_list})


def getDatatable(query):
    data_list = []
    col_names = []
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchall();
    col_names = [i[0] for i in cursor.description]
    col_names.append('Action')
    for eachval in fetchVal:
        delete_button = '<a class="delete-program-item tooltips" data-placement="top" href="#" data-original-title="Delete"  onclick="delete_entity(' + str(
            eachval[0]) + ')"><i class="fa fa-2x fa-trash-o"></i></a>'
        # delete_button = ''
        edit_button = '<a class="tooltips" data-placement="top" data-original-title="Edit Program" href="#" onclick="edit_entity(' + str(
            eachval[0]) + ');"><i class="fa fa-2x fa-pencil-square-o"></i></a>' + ' ' + delete_button
        eachval = eachval + (edit_button,)
        data_list.append(list(eachval))
    return json.dumps({'col_name': col_names, 'data': data_list})


'''
highcharts Graph Generation Functions Type Wise
'''





def get_member_chart(request):
    query = "SELECT  (select name from geo_ward where id=geo_ward_id) as category, sum(hh_member_number) as value FROM public.household group by geo_ward_id";
    jsondata = generate_json_bar_line_area_Chart('category', 'value', query)
    return HttpResponse(jsondata, content_type="application/json")




def getClusteredMap(query):
    jsondata={ "type": "FeatureCollection", "features": []}
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchall();
    for eachval in fetchVal:
        if eachval[0] is not None:
            eachjson=json.loads(json.dumps(eachval[0]))
            jsondata["features"].append(eachjson)
    return jsondata


@csrf_exempt
def generate_graph(request, graph_id):
    """
    From Ajax Request
    Router of Chart Generation
    :param request:
    :param graph_id:
    :return:
    """
    dashboardGenerator = DashboardGenerator.objects.filter(id=graph_id).first()
    jsondata = {}
    if dashboardGenerator.content_type == 0:  # GRAPH
        if dashboardGenerator.datasource_type == "1":  # 1 = QUERY
            query = get_filtered_query(request.POST, dashboardGenerator.datasource)
            highchartsConfig = HighchartsConfig(graph_id)
            jsondata = highchartsConfig.execute_query(dashboardGenerator.chart_type, query)
            #jsondata = execute_query(dashboardGenerator.chart_type.id, query)
        elif dashboardGenerator.datasource_type == "2":  # 2 = URL
            # TODO: URL will Return a json
            jsondata = HttpResponseRedirect(dashboardGenerator.datasource)
        else:  # 3 = JSON
            # TODO: URL will Return a json
            jsondata = dashboardGenerator.datasource

    elif dashboardGenerator.content_type == 1:  # TAble
        if dashboardGenerator.datasource_type == "1":  # 1 = QUERY
            query = get_filtered_query(request.POST, dashboardGenerator.datasource)
            jsondata = getDashboardDatatable(query)
        else:  # 2 = URL
            # TODO: URL will Return a json
            jsondata = json.dumps(HttpResponseRedirect(dashboardGenerator.datasource))

    else:  # MAP
        if dashboardGenerator.datasource_type == "1":  # 1 = QUERY
            query = get_filtered_query(request.POST, dashboardGenerator.datasource)
            return HttpResponse(json.dumps(getClusteredMap(query)))

        elif dashboardGenerator.datasource_type == "2":  # 2 = URL
            # TODO: URL will Return a json
            jsondata = HttpResponseRedirect(dashboardGenerator.datasource)
        else:  # Static JSON
            jsondata = dashboardGenerator.datasource
        return HttpResponse(jsondata)

    return HttpResponse(jsondata, content_type="application/json")


def execute_query(chart_type, query):
    # TODO Add more Chart type and check before excuting
    jsondata = ''
    if chart_type == 1 or chart_type == 3:
        jsondata = generate_json_column_area_chart('name', 'category', 'value', query)
    else:
        jsondata = generate_json_bar_line_area_Chart('category', 'value', query)
    return jsondata;


def get_filtered_query(post_dict, query):
    '''
    :param post_dict: Filtered OPtion with value
    :param query: Query with Filtering Option
    :return: filterted final query
    '''
    keyward_param = ""

    #Filtering Options need to be replaced in query
    print post_dict
    for key in post_dict:

        keyward_param = "@" + key
        #param_val =post_dict[key]
        param_val =post_dict.getlist(key)
        print post_dict.get(key)
        if len(param_val)==1:
            param_val = post_dict.get(key)
            if param_val:
                param_val="'"+ post_dict.get(key)+"'"
        else :
            coated_param_val=[]
            for val in param_val:
                coated_param_val.append("'"+val+"'")
            param_val=",".join(coated_param_val)

        if keyward_param in query and param_val:
            print keyward_param, "  ", param_val
            query = query.replace(keyward_param, param_val)

        keyward_param="@col_"+key
        if keyward_param in query:
            print keyward_param, "  ", post_dict.get(key)
            query = query.replace(keyward_param, post_dict.get(key))

    #Left over @name need to be replace with NULL
    words_starting_with_at = re.findall(r'@\w+', query)
    for w in words_starting_with_at:
        query=query.replace(w, 'NULL')

    print query

    return query


def on_change_element(request):
    """
    On change for Single Select Cascading
    :param request:
    :return:
    """
    control_id = request.POST.get("control_id")
    changed_val = request.POST.get("changed_val")
    controls_js = ''
    cascaded_elements = DashboardControlsGenerator.objects.filter(cascaded_by_id=control_id).first()
    parent_div_id = cascaded_elements.allignment + '_' + str(cascaded_elements.id)
    cursor = connection.cursor()
    onchange_function_js = ""
    cursor.execute(cascaded_elements.datasource.replace("@id", changed_val))
    cascaded_elements_next = DashboardControlsGenerator.objects.filter(cascaded_by_id=cascaded_elements.id).first()
    if cascaded_elements_next is not None:
        onchange_function_js = 'onChangeElement(' + str(control_id) + ');'
    row = cursor.fetchone()

    ds_data = utility_functions.unicodoToString(row[0])
    # controls_js += '\nvar jsondata_' + str(cascaded_elements.id) + '=JSON.parse(' + json.dumps(row[ 0]) + ');\n dropdownControlCreate("' + cascaded_elements.control_id + '","' + parent_div_id + '","' + cascaded_elements.control_name + '","' + cascaded_elements.control_label + '","' + onchange_function_js + '", jsondata_' + str(cascaded_elements.id) + ' );'
    # jsondata={"jsondata":row[0], "element": cascaded_elements.control_id ,"parent_div_id": parent_div_id , "control_name": cascaded_elements.control_label ,"control_label": cascaded_elements.control_name, "has_cascaded_element":onchange_function_js  }
    jsondata = {"jsondata": ds_data, "element": cascaded_elements.control_id}

    return HttpResponse(json.dumps(jsondata), content_type="application/json")


def on_change_multiple_select(request):
    """
    On change for Multiple Select Cascading
    :param request:
    :return:
    """
    control_id = request.POST.get("control_id")
    changed_vals = request.POST.getlist("changed_val[]")

    controls_js = ''

    coated_param_val = []
    for val in changed_vals:
        coated_param_val.append("'" + val + "'")

    changed_val = ",".join([str(item) for item in coated_param_val])
    cascaded_elements = DashboardControlsGenerator.objects.filter(cascaded_by_id=control_id).first()
    parent_div_id = cascaded_elements.allignment + '_' + str(cascaded_elements.id)
    cursor = connection.cursor()
    onchange_function_js = ""
    #updateted_datasource = cascaded_elements.datasource.replace("::text", "::integer")
    updateted_datasource = cascaded_elements.datasource
    print updateted_datasource.replace("@id", " in(" + changed_val + ") ")
    cursor.execute(updateted_datasource.replace("@id", " in(" + changed_val + ") "))
    cascaded_elements_next = DashboardControlsGenerator.objects.filter(cascaded_by_id=cascaded_elements.id).first()
    if cascaded_elements_next is not None:
        onchange_function_js = 'onChangeMultipleSelect(' + str(control_id) + ');'
    row = cursor.fetchone()
    ds_data = utility_functions.unicodoToString(row[0])
    # print json.dumps(cascaded_elements), '  JSON  '
    # controls_js += '\nvar jsondata_' + str(cascaded_elements.id) + '=JSON.parse(' + json.dumps(row[ 0]) + ');\n dropdownControlCreate("' + cascaded_elements.control_id + '","' + parent_div_id + '","' + cascaded_elements.control_name + '","' + cascaded_elements.control_label + '","' + onchange_function_js + '", jsondata_' + str(cascaded_elements.id) + ' );'
    # jsondata={"jsondata":row[0], "element": cascaded_elements.control_id ,"parent_div_id": parent_div_id , "control_name": cascaded_elements.control_label ,"control_label": cascaded_elements.control_name, "has_cascaded_element":onchange_function_js  }
    jsondata = {"jsondata": ds_data, "element": cascaded_elements.control_id}
    return HttpResponse(json.dumps(jsondata), content_type="application/json")


"""
FILTERING CONTROL CREATE
"""


class FilteringControl():
    """
    Add Filtering Control
    """

    def __init__(self, nav_id):
        self.nav_id = nav_id
        self.parent_div_id = ''
        self.controls_js = ''
        self.controls_html = '<div id="right_' + str(
            nav_id) + '" class="mpower-section right sidenav sidenav_right"><a  href="javascript:void(0)"  class="closebtn " onclick="closeNav(\'right_' + str(
            nav_id) + '\');">&times;</a>  </div> <a  href="#" id="right_link_' + str(
            nav_id) + '"  onclick="openNav(\'right_' + str(nav_id) + '\',\'container_' + str(
            nav_id) + '\');"  style="display:none;"  ><i class="fa fa-filter"></i></a> '

    def get_content(self):

        control_defs = DashboardControlsGenerator.objects.filter(navigation_bar_id=self.nav_id).order_by(
            'element_order')

        def func_not_found():  # just in case we dont have the function
            print "No Function Found!"

        for control_def in control_defs:
            self.parent_div_id = control_def.allignment + '_' + str(self.nav_id)
            self.controls_js += '$("#' + control_def.allignment + '_link_' + str(self.nav_id) + '").show();\n'
            control_func_name = control_def.control_type
            control_function = getattr(self, control_func_name, func_not_found)
            control_function(control_def)

        result = {'controls_html': self.controls_html, 'controls_js': self.controls_js}
        return result

    def single_select(self, control_def):
        """
        Single Select Create HTML AND JS
        :return: JSON including 2 attributes:  'controls_html', 'controls_js'
        """
        onchange_function_js = ''
        cursor = connection.cursor()
        #if control_def.cascaded_by is None:
        #    cursor.execute(control_def.datasource.replace("@id", "%"))
        #else:
        #    cursor.execute(control_def.datasource.replace("@id", ""))
        cursor.execute(control_def.datasource.replace("@id", "%"))
        cascaded_elements = DashboardControlsGenerator.objects.filter(cascaded_by_id=control_def.id).first()
        if cascaded_elements is not None:
            onchange_function_js = 'var changed_val= $(this).val();onChangeElement(' + str(
                control_def.id) + ',changed_val);'
        row = cursor.fetchone()
        ds_data = utility_functions.unicodoToString(row[0])

        if control_def.appearance=="":
            appearance = "{}"
        else:
            appearance = control_def.appearance
        #print appearance
        self.controls_js += '\nvar jsondata_' + str(control_def.id) + '=JSON.parse(' + json.dumps(
            ds_data) + ');\n dropdownControlCreate("' + control_def.control_id + '","' + self.parent_div_id + '","' + control_def.control_name + '","' + control_def.control_label + '","' + onchange_function_js + '", jsondata_' + str(
            control_def.id) + ', '+ appearance+' );'

    def multiple_select(self, control_def):
        """
        Multiole Select Create HTML AND JS
        :return: JSON including 2 attributes:  'controls_html', 'controls_js'
        """
        cursor = connection.cursor()
        onchange_function_js = ''
        ds_data = '[]'
        if control_def.datasource_type == '1':
            cursor.execute(control_def.datasource.replace("@id", "like '%'"))
            cascaded_elements = DashboardControlsGenerator.objects.filter(cascaded_by_id=control_def.id).first()
            if cascaded_elements is not None:
                onchange_function_js = ' var changed_val= $(this).val(); onChangeMultipleSelect(' + str(
                    control_def.id) + ',changed_val);'
            row = cursor.fetchone()
            ds_data = utility_functions.unicodoToString(row[0])
        if control_def.datasource_type == '3':
            ds_data = control_def.datasource
        if control_def.appearance=="":
            appearance = "{}"
        else:
            appearance = control_def.appearance
        self.controls_js += '\nvar jsondata_' + str(control_def.id) + '=JSON.parse(' + json.dumps(
            ds_data) + ');\n multipleSelectControlCreate("' + control_def.control_id + '","' + self.parent_div_id + '","' + control_def.control_name + '",  "' + control_def.control_label + '"  ,"' + onchange_function_js + '", jsondata_' + str(
            control_def.id) + ', '+appearance+');'

    def checkbox(self, control_def):
        """
        Checkbox Create HTML AND JS
        :return: None
        """
        cursor = connection.cursor()
        cursor.execute(eachrow.datasource)
        row = cursor.fetchone()
        ds_data = utility_functions.unicodoToString(row[0])
        self.controls_js += '\nvar jsondata_' + str(control_def.id) + '=JSON.parse(' + json.dumps(
            ds_data) + ');\n checkboxControlCreate("' + control_def.control_id + '","' + self.parent_div_id + '","' + control_def.control_name + '","' + control_def.control_label + '", jsondata_' + str(
            control_def.id) + ' );'

    def radio(self, control_def):
        """
        Radio Create HTML AND JS
        :return: None
        """
        # controls_html += '<div id="' + parent_div_id + '"></div>'
        cursor = connection.cursor()
        cursor.execute(control_def.datasource)
        row = cursor.fetchone()
        ds_data = utility_functions.unicodoToString(row[0])
        self.controls_js += '\nvar jsondata_' + str(control_def.id) + '=JSON.parse(' + json.dumps(
            ds_data) + ');\n radioControlCreate("' + control_def.control_id + '","' + self.parent_div_id + '","' + control_def.control_name + '","' + control_def.control_label + '", jsondata_' + str(
            control_def.id) + ' );'

    def date(self, control_def):
        """
        Date Create HTML AND JS
        :return: None
        """
        if control_def.appearance == "":
            control_def.appearance = '{"format":"dd-mm-yyyy","viewmode":"days","minviewmode":"days", "minviewmode":"years"}'
        self.controls_js += '\n dateControlCreate("' + control_def.control_id + '","' + self.parent_div_id + '","' + control_def.control_name + '","' + control_def.control_label + '",' + control_def.appearance + ', ""  );'

    def button(self, control_def):
        """
        Button Create HTML AND JS
        :return: None
        """
        self.controls_js += '\n buttonControlCreate("' + control_def.control_id + '","' + self.parent_div_id + '", "' + control_def.control_label + '" );'

    def text(self, control_def):
        """
        Text Box Create HTML AND JS
        :return: None
        """
        self.controls_js += '\n textinputControlCreate("' + control_def.control_id + '","' + self.parent_div_id + '","' + control_def.control_name + '","' + control_def.control_label + '", ""  );'


"""
********COMPONENT(Chart) CREATION********
"""


class Component:
    """
    Interface For Any Component, Ex- Graph, Table, Map ect
    """

    def execute(self):
        """
        :return: JSON having these attribute 'chart_html', 'js_chart_calling_function' ,'js_chart_calling_function_with_param'
        """
        pass


class Graph(Component):
    """
    Graph is a Component
    Its Taking Data from Chart Definition and making Required HTML and JS Functions
    """

    def __init__(self, chart_def):
        self.chart_html = ''
        self.js_chart_calling_function = ''
        self.js_chart_calling_function_with_param = ''
        self.chart_def = chart_def

    def execute(self):
        """
        Get HTML and JS for GRAPH
        :return: JSON
        """
        appearance = json.loads(self.chart_def.chart_object)
        width = "100%"
        customized=False
        if "width" in appearance:
            width = appearance["width"]

        if "customized" in appearance:
            customized = appearance["customized"]

        if customized==False:
            self.chart_html += '<div  style="width:' + str(width) + '%"  class="middle-item "><div  id="' + self.chart_def.element_id + '"></div></div>'
        self.js_chart_calling_function += '\nmpowerRequestForChart("' + self.chart_def.post_url + '", "' + self.chart_def.element_id + '", ' + self.chart_def.chart_object + ', {});'
        self.js_chart_calling_function_with_param += 'mpowerRequestForChart("' + self.chart_def.post_url + '", "' + self.chart_def.element_id + '", ' + self.chart_def.chart_object + ', parameters );'
        return {'chart_html': self.chart_html, 'js_chart_calling_function': self.js_chart_calling_function,
                'js_chart_calling_function_with_param': self.js_chart_calling_function_with_param}


class SimpleTable(Component):
    """
    SimpleTable is a Component
    Its Taking Data from Chart Definition and making Required HTML and JS Functions For SimpleTable Generation
    """

    def __init__(self, chart_def):
        self.chart_html = ''
        self.js_chart_calling_function = ''
        self.js_chart_calling_function_with_param = ''
        self.chart_def = chart_def

    def execute(self):
        """
        Get HTML and JS for table
        :return: JSON
        """
        appearance = json.loads(self.chart_def.chart_object)
        width = "100%"
        if "width" in appearance:
            width = appearance["width"];

        self.chart_html += '  <div style="width:' + str(
            width) + '%"  class="middle-item "><table id="' + self.chart_def.element_id + '"class="display table table-bordered table-striped table-condensed nowrap"></table></div>'
        self.js_chart_calling_function += '\nmpowerRequestForTable("' + self.chart_def.post_url + '", "' + self.chart_def.element_id + '", '+self.chart_def.chart_object+', {});'
        self.js_chart_calling_function_with_param += 'mpowerRequestForTable("' + self.chart_def.post_url + '", "' + self.chart_def.element_id + '",'+self.chart_def.chart_object+', parameters );'

        return {'chart_html': self.chart_html, 'js_chart_calling_function': self.js_chart_calling_function,
                'js_chart_calling_function_with_param': self.js_chart_calling_function_with_param}


class SimpleMap(Component):
    """
    SimpleMap is a Component
    Its Taking Data from Chart Definition and making Required HTML and JS Functions For SimpleMap Generation
    """

    def __init__(self, chart_def):
        self.chart_html = ''
        self.js_chart_calling_function = ''
        self.js_chart_calling_function_with_param = ''
        self.chart_def = chart_def

    def execute(self):
        appearance = json.loads(self.chart_def.chart_object)
        width = "100%"
        if "width" in appearance:
            width = appearance["width"];

        self.chart_html += '<div style="width:' + str( width) + '%" class="map" id="' + self.chart_def.element_id + '"></div> <div id="legend" class="legend"></div> '
        self.js_chart_calling_function += '\nmpowerRequestForMap("' + self.chart_def.post_url + '", "' + self.chart_def.element_id + '",  ' + self.chart_def.chart_object + ', {});'
        self.js_chart_calling_function_with_param += 'mpowerRequestForMap("' + self.chart_def.post_url + '", "' + self.chart_def.element_id + '",  ' + self.chart_def.chart_object + ', parameters );'

        return {'chart_html': self.chart_html, 'js_chart_calling_function': self.js_chart_calling_function,
                'js_chart_calling_function_with_param': self.js_chart_calling_function_with_param}



class CustomizedComponent(Component):
    """
    CustomizedComponent is a Component
    Its Reading HTML AND JS Directly from DB
    """

    def __init__(self, chart_def):
        self.chart_html = ''
        self.js_chart_calling_function = ''
        self.js_chart_calling_function_with_param = ''
        self.chart_def = chart_def

    def execute(self):
        appearance = json.loads(self.chart_def.chart_object)
        width = "100%"
        if "width" in appearance:
            width = appearance["width"]

        self.chart_html += '<div id="'+self.chart_def.element_id+'" style="width:' + str(width) + '%" class="middle-item ">'+self.chart_def.html_code+'</div>'
        if self.chart_def.js_code is not None:
            if "@parameter" in self.chart_def.js_code:
                global_caller=self.chart_def.js_code
                filter_caller=self.chart_def.js_code
                global_caller=global_caller.replace("@parameter", "{}")
                filter_caller=filter_caller.replace("@parameter", "parameters")
                self.js_chart_calling_function += global_caller
                self.js_chart_calling_function_with_param += filter_caller
            else:
                self.js_chart_calling_function += self.chart_def.js_code
                self.js_chart_calling_function_with_param +=  self.chart_def.js_code

        return {'chart_html': self.chart_html, 'js_chart_calling_function': self.js_chart_calling_function,
                'js_chart_calling_function_with_param': self.js_chart_calling_function_with_param}




class ComponentManager:
    """
    Create COMPONENT/ CHART For each navigation Tab
    """

    def __init__(self, nav_id):
        self.nav_id = nav_id
        self.components = []
        self.chart_html = ''
        self.js_chart_calling_function = ''
        self.js_chart_calling_function_with_param = ''

    def get_chart_content(self):
        """
        GET ALL HTML and JS Content
        :return: JSON having these attribute 'chart_html', 'js_chart_calling_function' ,'js_chart_calling_function_with_param'
        """

        chart_defs = DashboardGenerator.objects.filter(navigation_bar_id=self.nav_id).order_by('content_order')
        # chart_defs = DashboardGenerator.objects.filter(id=32).order_by('content_order')

        for chart_def in chart_defs:
            if chart_def.content_type == 0:  # GRAPH
                self.components.append(Graph(chart_def))
            elif chart_def.content_type == 1:  # Table
                self.components.append(SimpleTable(chart_def))
            elif chart_def.content_type == 2:  # MAP
                self.components.append(SimpleMap(chart_def))
            elif chart_def.content_type == 3:  # Customized Component
                self.components.append(CustomizedComponent(chart_def))

        for c in self.components:
            jsondata = c.execute()
            self.chart_html += jsondata['chart_html']
            self.js_chart_calling_function += jsondata['js_chart_calling_function']
            self.js_chart_calling_function_with_param += jsondata['js_chart_calling_function_with_param']

        return {'chart_html': self.chart_html, 'js_chart_calling_function': self.js_chart_calling_function,
                'js_chart_calling_function_with_param': self.js_chart_calling_function_with_param}



class HighchartsConfig():
    """
    HighCharts Functions.
    Creating JOSN for different charts
    """

    def __init__(self, graph_id):
        self.graph_id = graph_id


    def func_not_found(name_field, category_field, data_field, query):
        """
        Error Handler for Function calling from String
        """
        print "Exp: No Function Found!"
        return {}

    def execute_query(self,chart_type, query):
        # TODO Add more Chart type and check before excuting
        jsondata = ''
        dashboardGenerator = DashboardGenerator.objects.filter(id=self.graph_id).first()
        control_func_name = chart_type.function_name

        # GET DS Manipulator FUNCTION Name
        datasource_manipulator_func_name=getattr(self, dashboardGenerator.datasource_manipulator_func)
        df=datasource_manipulator_func_name(query)
        #GET CHART GENERATOR FUNCTION
        control_function = getattr(self, control_func_name)
        #jsondata = control_function(df)
        jsondata = control_function('name','category','value',df)
        return jsondata;

    def date_handler(self,obj):
        return obj.isoformat() if hasattr(obj, 'isoformat') else obj

    def decimal_default(self,obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        raise TypeError

    def getUniqueValues(self,dataset, colname):
        list = [];

        for dis in dataset:
            if dis[colname] in list:
                continue;
            else:
                list.append(dis[colname]);
        return list;


    def get_default(self,query):
        '''
        Use this function
        WHEN QUERY OUTPUT IS LIKE
        name|category|value
        'Afrin'|'2017'|5.00
        'Arian'|'2016'|6.00
        ..................
        .................

        :param query:
        :return: panda dataframe. Structure
        name|category|value
        ..................
        ...................


        '''
        df = pd.read_sql(query, connection)
        return df

    def get_transposed_df(self,query):
        '''
        Use this function
        WHEN QUERY OUTPUT IS LIKE
        col_1  | col_2|col_3 |..................
        33     | 2017 | 5.00 |


        :param query:
        :return: panda dataframe. Structure
        category|value
        col_1   |33
        col_2   |2017
        col_3   |5.00
        .............
        ............

        '''
        df = pd.read_sql(query, connection)
        df=df.T
        df['category'] = df.index
        df.columns=['value','category']
        return df


    def generate_json_bar_line_area_Chart(self,name_field, category_field, data_field,df):
        """
        Line Chart
        Horizontal Bar Chart
        Basic Area Chart
        @author:Emtious
        :param category_field:
        :param data_field:
        :param query:
        :return:
        """
        #category_field='category'
        #data_field='value'
        seriesData = []
        category_list = ""
        category_list = df[category_field].values.tolist()
        dict = {}
        dict['data']=df[data_field].values.tolist()
        seriesData.append(dict)

        jsonForChart = json.dumps({'categories': category_list, 'seriesdata': seriesData}, default=self.decimal_default)
        return jsonForChart


    def generate_json_column_area_chart(self, name_field, category_field, data_field,dataframe):
    #def generate_json_column_area_chart(self, dataframe):
        """
        Percentage Area Chart
        Multiple Area chart
        :param name_field:
        :param category_field:
        :param data_field:
        :param query:
        :return:
        """
        df=dataframe
        seriesData = []
        category_list = ""
        #category_field = 'category'
        #data_field = 'value'
        #name_field = 'name',
        #df = pd.read_sql("with p as(with t as(SELECT name_wmg,extract(year from event_date::date) yr,extract(month from event_date::date) mn, round((rank1_pm11+rank1_pm12+rank1_pm13+rank1_pm14+rank1_pm15+rank1_pm16+rank1_pm17+rank2_pm21+rank2_pm22+rank2_pm23+rank2_pm24+rank2_pm25+rank2_pm26+rank3_pm31+rank3_pm32+rank3_pm33+rank4_pm41+rank4_pm42+rank4_pm43+rank4_pm44)*100.0/60.0,2) qualification FROM vwparticipatory_monitoring  where  (zon::integer in (NULL) OR (NULL) IS NULL ) and  (district::integer  in (NULL) OR (NULL) IS NULL ) and (polder in (NULL) OR (NULL) IS NULL ) and (extract(year from event_date::date)=NULL OR NULL IS NULL )  )  select name_wmg,yr,(case when mn<7 then 'Jan-Jun' else 'Jul-Dec' end) mn,(case when mn<7 then yr+0.5 else yr+0.9 end)  sorting ,(case when qualification>=80 then 'Excellent' when qualification>=60 then 'Good' when qualification>=40 then 'Medium' else 'Bad' end) qualification, (case when qualification>=80 then '#058dc7' when qualification>=60 then '#dddf00' when qualification>=40 then '#50b432' else '#ed561b' end) as colors from t) select sorting,colors,qualification as name,(mn||','||(yr::text)) category,count(distinct name_wmg) as value from p group by qualification,yr,mn,colors,sorting order by sorting", connection)
        # Checking if colors already given ion dataset
        if df.empty == False:
            if "colors" not in df:
                df = df.pivot(index=name_field, columns=category_field, values=data_field)
                df = df.fillna(0)
                category_list = list(df.columns.values)
                for row in df.iterrows():
                    dict = {}
                    index, data = row
                    dict['name'] = index
                    dict['data'] = data.tolist()
                    seriesData.append(dict)
            else:
                df = pd.pivot_table(df, values=data_field, rows=[name_field, "colors"], cols=["sorting", category_field])
                df = df.fillna(0)
                category_list = []

                for data in df.columns.values:
                    category_list.append(data[1])

                for row in df.iterrows():
                    dict = {}
                    index, data = row
                    dict['name'] = index[0]
                    dict['data'] = data.tolist()
                    dict['color'] = index[1]
                    seriesData.append(dict)

        jsonForChart = json.dumps({'categories': category_list, 'seriesdata': seriesData}, default=self.decimal_default)
        return jsonForChart



    def generate_json_pie_chart(self, query):
        """
        Pie Chart
        :param name_field:
        :param category_field:
        :param data_field:
        :param query:
        :return:
        """
        category_field = 'category'
        data_field = 'value'
        name_field = 'name',
        dataset = utility_functions.db_fetch_values_dict(query)
        seriesData = []
        for data in dataset:
            dict = {}
            dict['name'] = data[name_field]
            dict['y'] = data[data_field]
            seriesData.append(dict)

        jsonForChart = json.dumps({'seriesdata': [{'name': name_field, 'data': seriesData}]}, default=self.decimal_default)

        return jsonForChart


"""
END OF Highcharts Config
"""


def generate_dynamic_report(request):
    """
    Generate Dynamic Report From saved Data
    :param request:
    :return:
    """

    # Get parent navigation titles
    MODULE_NAME = 'dashboard'
    navigationBarParent = DashboardNavigationBar.objects.filter(parent_link_id__isnull=True)
    sub_navigation = ''
    # get parent;s child
    navigation_bars = '<div class="portlet-body" ><ul class="nav nav-pills">'
    content_tabs = '<div class="tab-content ">'
    html_code = ''
    js_code = ''
    css_active = 'active'

    for eachrow in navigationBarParent:
        sub_navigation = ''
        navigationBarChild = DashboardNavigationBar.objects.filter(parent_link_id=eachrow.id)
        init_tab_caller = ''

        if not navigationBarChild:
            navigation_bars += '<li class="' + css_active + '"><a data-toggle="tab" onclick="init_tab_' + str(
                eachrow.id) + '();" href="#tab_' + str(eachrow.id) + '">' + eachrow.link_name + '</a></li>'
            content_tabs += '<div class="tab-pane ' + css_active + '" id="tab_' + str(
                eachrow.id) + '"  ><form id="form_' + str(
                eachrow.id) + '" > <div  class="flex "> <div  id="left_' + str(
                eachrow.id) + '" class="mpower-section left sidenav sidenav_left" ><a href="javascript:void(0)" class="closebtn" onclick="closeNav(\'left_' + str(
                eachrow.id) + '\');">&times;</a>   </div>  <a  href="#"   style="display:none;" id="left_link_' + str(
                eachrow.id) + '"    onclick="openNav(\'left_' + str(
                eachrow.id) + '\');"    ><i class="fa fa-filter"></i></a><div  id="middle_' + str(
                eachrow.id) + '" class="mpower-section middle " >'

            # Creating Filtering Control for each tab
            filteringControl = FilteringControl(eachrow.id)
            controls_info = filteringControl.get_content()

            # Creating CHART/Component for each tab
            componentManager = ComponentManager(eachrow.id)
            chart_content = componentManager.get_chart_content()

            js_code += 'function init_tab_' + str(eachrow.id) + '() { if ($("#container_' + str(
                eachrow.id) + '").data("load")=="unloaded") {  ' + controls_info['controls_js'] + '  ' + chart_content[
                           'js_chart_calling_function'] + ' \n $("#container_' + str(
                eachrow.id) + '").data("load","loaded"); }   }\n\n'
            content_tabs += ' <div class="mpower-section middle-top" >  <div class="form-group" id="top_' + str(
                eachrow.id) + '"> </div>  </div><div data-load="unloaded" class="middle-container" id="container_' + str(
                eachrow.id) + '">' + chart_content['chart_html'] + ' </div></div>' + controls_info['controls_html']
            content_tabs += '</div></form></div>'
            js_code += '$("#form_' + str(
                eachrow.id) + '").submit(function(event) { event.preventDefault(); var parameters = $(this).serializeArray(); console.log("Data "+parameters); \n ' + \
                       chart_content['js_chart_calling_function_with_param'] + ' });'

            if css_active == 'active':
                init_tab_caller = 'init_tab_' + str(eachrow.id) + '(); \n'
                css_active = ''
        else:
            sub_navigation = '<li class="dropdown ' + css_active + '"><a   href="#" class="dropdown-toggle" data-toggle="dropdown" id="tabDrop_' + str(
                eachrow.id) + '">' + eachrow.link_name + ' <i class="fa fa-angle-down"></i></a> <ul  class="dropdown-menu" role="menu" aria-labelledby="tabDrop_' + str(
                eachrow.id) + '" >'
            for eachchildrow in navigationBarChild:
                # dashboardGenerator = DashboardGenerator.objects.filter(navigation_bar_id=eachchildrow.id).first()
                sub_navigation += '<li class="' + css_active + '"><a onclick="init_tab_' + str(
                    eachchildrow.id) + '();" href="#tab_' + str(
                    eachchildrow.id) + '"  tabindex="-1" data-toggle="tab" >' + eachchildrow.link_name + '</a></li>'
                content_tabs += ' <div class="tab-pane ' + css_active + '" id="tab_' + str(
                    eachchildrow.id) + '"> <form id="form_' + str(
                    eachchildrow.id) + '" > <div  class="flex"> <div class="mpower-section left  sidenav sidenav_left "  id="left_' + str(
                    eachchildrow.id) + '" ><a href="javascript:void(0)" class="closebtn" onclick="closeNav(\'left_' + str(
                    eachchildrow.id) + '\');">&times;</a> </div><a  href="#" style="display:none;" id="left_link_' + str(
                    eachchildrow.id) + '"   onclick="openNav(\'left_' + str(
                    eachchildrow.id) + '\');"    ><i class="fa fa-filter"></i></a>  <div class="mpower-section middle"  id="middle_' + str(
                    eachchildrow.id) + '" > '

                # Creating Filtering Control for each tab
                filteringControl = FilteringControl(eachchildrow.id)
                controls_info = filteringControl.get_content()

                # Creating CHART/Component for each tab
                componentManager = ComponentManager(eachchildrow.id)
                chart_content = componentManager.get_chart_content()

                js_code += 'function init_tab_' + str(eachchildrow.id) + '() {  if($("#container_' + str(
                    eachchildrow.id) + '").data("load")=="unloaded") {  ' + controls_info['controls_js'] + '  ' + \
                           chart_content['js_chart_calling_function'] + '\n $("#container_' + str(
                    eachchildrow.id) + '").data("load","loaded");   } }\n\n'
                content_tabs += '<div class="mpower-section middle-top"  > <div class="form-group"  id="top_' + str(
                    eachchildrow.id) + '"> </div> </div><div data-load="unloaded" class="middle-container" id="container_' + str(
                    eachchildrow.id) + '">' + chart_content['chart_html'] + '</div></div>' + controls_info[
                                    'controls_html']
                content_tabs += ' </div></form></div>'
                js_code += '$("#form_' + str(
                    eachchildrow.id) + '").submit(function(event) { event.preventDefault(); var parameters = $(this).serializeArray(); console.log("Data "+parameters); \n ' + \
                           chart_content['js_chart_calling_function_with_param'] + ' });'

                if css_active == 'active':
                    init_tab_caller = 'init_tab_' + str(eachchildrow.id) + '(); \n'
                    css_active = ''
            sub_navigation += '</ul>  </li>'

        css_active = ''
        js_code += init_tab_caller
        navigation_bars += sub_navigation
    content_tabs += '</div>'
    navigation_bars += '</ul>' + content_tabs + '</div>'

    return {'html_code': navigation_bars, 'js_code': js_code}


def generate_saved_report(request, id):
    """
    Generate Report From saved Data
    :param request:
    :param id:
    :return:
    """
    json_output = {}
    if id == "0":
        json_output = generate_dynamic_report(request)
    else:
        loaded_dashboard_instance = DashboardLoader.objects.get(pk=id)
        json_output = {'html_code': loaded_dashboard_instance.html_code, 'js_code': loaded_dashboard_instance.js_code}

    return render(request, "dashboard/generate_saved_report.html", json_output)


'''
******************  Save Current Template ***********************
'''


def save_loaded_dashboard(request):
    """
    Save Current Dynamic Dashboard
    :param request:
    :return:
    """

    generated_saved_report = generate_dynamic_report(request)
    if request.method == "POST":

        try:
            dashboardLoader = DashboardLoader()
            dashboardLoader.html_code = generated_saved_report['html_code']
            dashboardLoader.js_code = generated_saved_report['js_code']
            dashboardLoader.name = request.POST.get("dashboard_name")
            dashboardLoader.save()
            messages.success(request, '<i class="fa fa-check-circle"></i> Dashboard Saved Successfully',
                             extra_tags='alert-success crop-both-side')
        except:
            messages.success(request, '<i class="fa fa-cross-circle"></i> Dashboard saving failed.',
                             extra_tags='alert-danger crop-both-side')
        return index(request)


def show_template_get_json(request):
    """
    Show List of Saved Template
    :param request:
    :return:
    """
    datajson = getDatatable(
        'select id ,\'<a href="/dashboard/generate_saved_report/\' || id::text || \'/">\' || name ::text || \'</a> \' as name , created_at::text as Date from dashboard_loader order by created_at desc')
    return HttpResponse(datajson, content_type='application/json')


def update_loaded_dashboard(request, loaded_db_id):
    """
    Update loaded_dashboard
    :param request:
    :param loaded_db_id:
    :return:
    """
    LOADED_DASHBOARD_ID = loaded_db_id
    if request.method == "GET":
        loaded_dashboard_form_instance = DashboardLoader.objects.filter(id=LOADED_DASHBOARD_ID).first()
        loaded_dashboard_form = DashboardLoaderUpdateForm(instance=loaded_dashboard_form_instance)
        context = {
            "loaded_dashboard_form": loaded_dashboard_form,
            "LOADED_DASHBOARD_ID": LOADED_DASHBOARD_ID
        }
    if request.method == "POST":
        loaded_dashboard_form_instance = DashboardLoader.objects.filter(id=loaded_db_id).first()
        loaded_dashboard_form = DashboardLoaderUpdateForm(data=request.POST, instance=loaded_dashboard_form_instance)
        if loaded_dashboard_form.is_valid():
            loaded_dashboard_form_instance = loaded_dashboard_form.save()
            messages.success(request, '<i class="fa fa-check-circle"></i> Dashboard Saved Successfully',
                             extra_tags='alert-success crop-both-side')
            return index(request)
        else:
            messages.success(request, '<i class="fa fa-cross-circle"></i> Dashboard saving failed. Please Try again.',
                             extra_tags='alert-danger crop-both-side')
            context = {
                "loaded_dashboard_form": loaded_dashboard_form,
                "LOADED_DASHBOARD_ID": LOADED_DASHBOARD_ID
            }
            return render(request, "dashboard/update_loaded_dashboard.html", context, status=500);
    return render(request, "dashboard/update_loaded_dashboard.html", context);


def delete_loaded_dashboard(request, loaded_db_id):
    """
    Delete Loaded Dashboard
    :param request:
    :param loaded_db_id:
    :return:
    """
    loaded_dashboard_instance = DashboardLoader.objects.get(pk=loaded_db_id)
    try:
        loaded_dashboard_name = loaded_dashboard_instance.name;
        loaded_dashboard_instance.delete()
        data = getAjaxMessage("success",
                              '<i class="fa fa-check-circle"></i> Dashboard -' + loaded_dashboard_name + ' has been deleted successfully!')
    except ProtectedError:
        loaded_dashboard_del_message = "Dashboard could not be deleted."
        data = getAjaxMessage("danger", loaded_dashboard_del_message)
    return HttpResponse(simplejson.dumps(data), content_type="application/json")



"""
Project Specefic Functions
Blue Gold
"""



def get_json(query,coulumns):
    df = pd.read_sql(query,connection)
    df = df.T
    df['x'] = df.index
    df = df[df.columns[::-1]]
    df.columns = coulumns
    df = df.to_json(orient='split')
    return df




def get_wmg_tracker_Excel(request,json_data):

    data = json_data
    tables = data.get('data')
    wb = xlwt.Workbook()
    ws = wb.add_sheet("My Sheet", cell_overwrite_ok=True)
    countLine = 0;
    for t in tables:
        ws.write(countLine, 0, t[1])
        subtables = data.get('subtables')
        table = subtables.get(t[1])
        countLine+=2

        table = json.loads(table)
        columns = table.get('columns')
        colcount= len(columns)
        for j, col in enumerate(columns):
            ws.write(countLine, j, col)
        countLine+=1
        tabledata = table.get('data')
        for rowdata in tabledata:
            colLine=0
            for row in rowdata:
                ws.write(countLine, colLine, row)
                colLine+=1
            countLine+=1
        countLine+=2

    #current_user = UserModuleProfile.objects.filter(user=user)
    user_path_filename = os.path.join(settings.MEDIA_ROOT, request.user.username)
    user_path_filename = os.path.join(user_path_filename, "export_wmg_tracker")
    if not os.path.exists(user_path_filename):
        os.makedirs(user_path_filename)

    filename=os.path.join(user_path_filename, "WMG_Summery_Tracker_Report.xls")
    wb.save(filename)
    return filename


def getWMGTrackerExcel(request):
    """
    GET Excel of WMG Tracker Summery Report
    :param request:
    :return:
    """
    data = get_wmg_tracker_report_json(request.GET)
    path_filename = get_wmg_tracker_Excel(request,data)
    file_path = os.path.join(settings.MEDIA_ROOT, path_filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    return HttpResponse(status=404)


def get_wmg_tracker_report_json(post_dict):
    """
    Returnong JSON for get_wmg_tracker_report
    :param request:
    :return: json
    """
    filtering = " where (zon::integer in (@zone) OR (@zone) IS NULL ) and (district::integer in (@geo_district) OR (@geo_district) IS NULL )  and (polder::text in (@polder) OR (@polder) IS NULL ) "
    sections_name = ["Results of", "WMG Funds", "Use of WMG Funds", "Type of Business investment", "Training Course",
                     "Modules/ Topices for Learning Session", "Name of Crops",
                     "Initiatives Activities for Horizantal Learnng", "Name of Technologies and new parctices adopted",
                     "Collective Action for Economic Activities"]
    headers = []
    for names in sections_name:
        headers.append(["", names])
    headers_col = ["WMG Summary Report"]

    subtables = {}

    # Results of
    # View:: vwwmg_tracker_1_2
    section = sections_name[0]
    query = get_filtered_query(post_dict,
                               'select count( ta_ffs_no) as "No. of TA-FFS conducted", sum(ta_ffs_male) as "No. of enrolled TA-FFS male members"   ,  sum(ta_ffs_female) as "No. of enrolled TA-FFS female members"   ,  ((sum(ta_ffs_female)/(sum(ta_ffs_female)+sum(ta_ffs_male)))*100) as "% of TA FFS female members"   ,  count(dae_ffs_no) as "No. of DAE-FFS conducted"   ,  sum(dae_ffs_male) as "No. of enrolled DAE-FFS male members"   ,  sum(dae_ffs_female) as "No. of enrolled DAE-FFS female members"   ,  ((sum(dae_ffs_female)/(sum(dae_ffs_male)+sum(dae_ffs_female)))*100) as "% of DAE FFS female members"   ,  count(mfs_no) as "No. of MFS conducted"   ,  sum(mfs_male) as "No. of enrolled MFS male members"   ,  sum(mfs_female) as "No. of enrolled MFS female members"   ,  ((sum(mfs_female)/(sum(mfs_male)+sum(mfs_female)))*100) as "% of MFS female members"   ,  count(lcs_group_no) as "No. of LCS groups formed"   ,  sum(lcs_male) as "No. of enrolled LCS male member"   ,  sum(lcs_female) as "No. of enrolled LCSFemale member"   ,  ((sum(lcs_female)/(sum(lcs_male)+sum(lcs_female)))*100) as "% of LCS female member"  from vwwmg_tracker_1_2  where (zon::integer in (@zone) OR (@zone) IS NULL ) and (district::integer in (@geo_district) OR (@geo_district) IS NULL )')
    subtables[section] = get_json(query, [section, "Progress"])


    # WMG Funds
    # View:: vwwmg_tracker_1_2
    section = sections_name[1]
    query = get_filtered_query(post_dict,
                               'select Sum(WMG_fund_addmission_fee) as "Admission fee (TK)"  , sum(WMG_fund_savings_male) as "Savings (Tk) from Male"  , sum(WMG_fund_savings_female) as "Savings (Tk) from Female"  , sum(WMG_fund_OM_fee_male) as "O&M fee (Tk) collected from Male"  , sum(WMG_fund_OM_fee_female) as "O&M fee (Tk) collected from female"  , sum(WMG_fund_miscell_fee_male) as "Miscellaneous Fees (Tk) collected from Male"  , sum(WMG_fund_miscell_fee_female) as "Miscellaneous Fees (Tk) collected from Female"  , sum(WMG_fund_profit) as "Undistributed Profit/Income (TK)"  , 0 as "Total WMG Funds (Tk)"   from vwwmg_tracker_1_2' + filtering)
    subtables[section] = get_json(query, [section, "Progress"])


    # Use of WMG Funds
    # View:: vwwmg_tracker_1_2
    section = sections_name[2]
    query = get_filtered_query(post_dict,
                               ' select Sum(WMG_fund_use_invest_IGA_amount) as "WMG fund invested in collective IGAs (TK) "  ,  Sum(use_WMG_fund_profit_distribute) as "Profit distributed (TK) "  ,  Sum(use_WMG_fund_bank_deposit) as "Deposit in Bank (Tk) "  ,  Sum(use_WMG_fund_expense) as "Expenditure of this month (Tk) "  ,  Sum(use_WMG_fund_cash_in_hand) as "Cask in hand (Tk) "  ,  Sum(use_WMG_fund_up_to_month_expens) as "Expenditure upto this month (Tk)"  from vwwmg_tracker_1_2' + filtering)
    subtables[section] = get_json(query, [section, "Progress"])


    # Type of Business investment
    # View:: vwbusiness_investment
    section = sections_name[3]
    query = get_filtered_query(post_dict,
                               'select business as "Type of Business investment", sum(wmg_fund_use_invest_iga_amount) as "No. of Person involved" , sum(wmg_fund_use_invest_iga_amount) as "Investment Amount" from vwbusiness_investment  ' + filtering + ' group by business')
    df = pd.read_sql(query, connection)
    df = df.to_json(orient='split')
    subtables[section] = df

    # Training Course
    # View:: vwtraining_course
    section = sections_name[4]
    query = get_filtered_query(post_dict,
                               'with t as( select course as "Training Course", sum(capacity_build_act_male) as "Male" , sum(capacity_build_act_female) as "Female" from vwtraining_course ' + filtering + '  group by course ) select t.*,("Male"+"Female") total,round(("Female"*100.00)/("Male"+"Female"),2) "% of Female Participants" from t')
    df = pd.read_sql(query, connection)
    df = df.to_json(orient='split')
    subtables[section] = df

    # Modules/ Topices for Learning Session
    # View:: vwwmg_tracker_1_2
    section = sections_name[5]
    query = get_filtered_query(post_dict,
                               'select module_topic as "Modules/ Topices for Learning Session", sum(module_learn_male) as "Male" , sum(module_learn_female) as "Female"  from vwmodules_learning_session  ' + filtering + ' group by module_topic ')
    df = pd.read_sql(query, connection)
    df = df.to_json(orient='split')
    subtables[section] = df

    # Name of Crops
    # View:: vwwmg_tracker_1_2
    section = sections_name[6]
    query = get_filtered_query(post_dict,
                               'select crop_name as "Name of Crops", sum(demons_crop_plot_own_male) as "Male" , sum(demons_crop_plot_own_female) as "Female"  from vwname_crop ' + filtering + '  group by crop_name')
    df = pd.read_sql(query, connection)
    df = df.to_json(orient='split')
    subtables[section] = df
    # Initiatives Activities for Horizantal Learnng
    # View:: vwwmg_tracker_1_2
    section = sections_name[7]
    query = get_filtered_query(post_dict,
                               'select activities as "Initiatives Activities for Horizantal Learnng", sum(horizontal_learning_act_male) as "Male" , sum(horizontal_learning_act_male) as "Female"  from vwinitiatives_activities_horizantal_learnng  ' + filtering + ' group by activities')
    df = pd.read_sql(query, connection)
    df = df.to_json(orient='split')
    subtables[section] = df

    # Name of Technologies and new parctices adopted
    # View:: vwwmg_tracker_1_2
    section = sections_name[8]
    query = get_filtered_query(post_dict,
                               'select technologies as "Name of Technologies and new parctices adopted", sum(wmg_mem_num) as "No. of WMG members"  from vwtechnologies_parctices_adopted  ' + filtering + ' group by technologies')
    df = pd.read_sql(query, connection)
    df = df.to_json(orient='split')
    subtables[section] = df

    # Collective Action for Economic Activities
    # View:: vwcollective_action_for_economic_activities
    section = sections_name[9]
    query = get_filtered_query(post_dict,
                               'select activities as "Collective Action for Economic Activities", sum(eco_act_male) as "No. of Male involved" , sum(eco_act_male) as "No. of Female involved", sum(eco_act_investment)  as "Investment in Tk" from vwcollective_action_for_economic_activities  ' + filtering + ' group by activities')
    df = pd.read_sql(query, connection)
    df = df.to_json(orient='split')
    subtables[section] = df

    data = {'col_name': headers_col, 'data': headers, 'subtables': subtables}
    return data

def get_wmg_tracker_report(request):
    """
    Blue Gold: WMG Tracker Summery Report
    WMG Tracker Form
    :return: JSON
    """
    data=get_wmg_tracker_report_json(request.POST)
    data = json.dumps(data)
    return HttpResponse(data)
