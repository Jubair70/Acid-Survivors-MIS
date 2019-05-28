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

from django.db import IntegrityError
from django.db.models import ProtectedError
from django.db import connection
import HTML
import datetime

from onadata.apps.usermodule.views_project import get_viewable_projects
from onadata.apps.usermodule.views import get_organization_by_user
from onadata.apps.usermodule.models import UserModuleProfile, Organizations
from onadata.apps.approval.models.approval import InstanceApproval


def get_report_operation_status(request):
    list_of_list = []
    startDate = ''
    endDate = ''
    submitter = '%'
    filter_org_id = '%'

    if request.method == 'POST':

        startDate = request.POST.get("start_date", "")
        endDate = request.POST.get("end_date", "")
        submitter = request.POST.get("submitter", "")
        filter_org_id = request.POST.get("org_id", "%")

    xforms = get_viewable_projects(request)
    # print xforms
    #print submitted_by
    c = connection.cursor()
    try:
        c.execute("BEGIN")
        c.callproc("approval_status",(str(startDate),str(endDate),str(submitter), str(filter_org_id)))
        results = c.fetchall()
        c.execute("COMMIT")
    finally:
        c.close()
    # print results
    for each in results: 
    	for xform in xforms:
    		if str(each[0]) == xform.id_string:
    			tmp_list = [xform.title,each[1],each[2],each[3],each[4]]
    			list_of_list.append(tmp_list) 
    
    # print list_of_list
    header_row=['Form','Submitted','Pending','Approved','Rejected']
    htmlcode = get_all_submitted_values_as_table(list_of_list,header_row)
    #print htmlcode
    submitted_by = InstanceApproval.objects.values_list('senderid',flat=True).distinct()
    org_id_list = get_organization_by_user(request.user)
    org_filter_list = {}
    for org_id in org_id_list:
        organization = get_object_or_404(Organizations, id=org_id)
        org_filter_list[org_id] = str(organization.organization)
    print ('org_list', org_id_list)
    print ('org_list', org_filter_list)
    variables = RequestContext(request, {
        'status_table': htmlcode,
        'submitted_by':submitted_by,
        'org_filter_list' : org_filter_list,
        })
    if request.is_ajax():
        return HttpResponse(htmlcode)
        
    output = render(request,'approval_status_summary.html',variables);
    return HttpResponse(output)

def get_all_submitted_values_as_table(data_list,table_headers):
    
    htmlcode = HTML.table(data_list,header_row=table_headers,col_width=['50%','10%' '10%', '10%', '10%'],col_align=['left', 'center','center', 'center', 'center']
    )
    return_html = str(htmlcode).replace('<TABLE', '<TABLE class="table table-bordered" id="sortable"')
    return return_html

def get_report_np_attendence_activity(request):
	table_headers_girls = ['Girls Group','10-12','13-15','16-18','19-24','Total Avg','Dalit','OEC','Janajati','Muslim']
	table_headers_boys = ['Boys Group','10-12','13-15','16-17','19-24','Total Avg','Dalit','OEC','Janajati','Muslim']
	table_headers_activities = ['Events','Male','Female','Total','Male Avg','Female Avg','Total Avg']
	data_list_activities = [
		['Parents Committee Meeting','0','0','0','0','0','0'],
		['VCPC Meeting','0','0','0','0','0','0'],
		['Parents Committee and VCPC Meeting','0','0','0','0','0','0']
		]
	
	pngo_name = '%'
	vdc_name = '%'
	sm_name = '%'
	month_from = '2016-01-01'
	month_to = datetime.datetime.now().strftime ("%Y-%m-%d")
	
	start_date ='2016-01-01'
	end_date = datetime.datetime.now().strftime ("%Y-%m-%d")

	if request.is_ajax():
		pngo_name = request.POST.get('pngo','%')
		vdc_name = request.POST.get('vdc','%')
		month_from = request.POST.get('start_date','2016-01-01')
		month_to = request.POST.get('end_date',datetime.datetime.now().strftime ("%Y-%m-%d"))
		sm_name = request.POST.get('sm_name','%')
		#print 'Ajax calling serve it...'
	question_name = []
	atten_boysGirl = []
	atten_week =[]
	atten_Age16_18 = []
	atten_Age13_15 =[]
	atten_Age10_12 =[]
	atten_Age19_24 = []
	atten_Dalit = []
	atten_Brahmin = []
	atten_Janajati = []
	atten_Muslim = []
	
	otherEvent_eventsAttendence = []
	otherEvent_Male = []
	otherEvent_Female = []

	raw_query = "select instance_parse_data.question,instance_parse_data.qvalue_json->>'question_value' as value from instance_parse_data,logger_instance where instance_parse_data.instance_id=logger_instance.id and"
	sub_query = " logger_instance.json->>'note/pngo'::text like '"+str(pngo_name)+"' and logger_instance.json->>'note/vdc'::text like '"+str(vdc_name)+"' and logger_instance.json->>'note/smName'::text like '%"+str(sm_name)+"%' and (logger_instance.json->>'_submission_time')::timestamp::date between '"+str(month_from)+"' and '"+str(month_to)+"' and (instance_parse_data.question like 'atten_boysGirl' or instance_parse_data.question like 'atten_week' or instance_parse_data.question like 'atten_Age10_12' or instance_parse_data.question like 'atten_Age13_15' or instance_parse_data.question like 'atten_Age16_18' or instance_parse_data.question like 'atten_Age19_24' or instance_parse_data.question like 'atten_Dalit' or instance_parse_data.question like 'atten_excludeCaste' or instance_parse_data.question like 'atten_Janajati' or instance_parse_data.question like 'atten_Muslim' or instance_parse_data.question like 'otherEvent_eventsAttendence' or instance_parse_data.question like 'otherEvent_Male' or instance_parse_data.question like 'otherEvent_Female')"
	full_query = raw_query+sub_query
	print full_query
	cursor = connection.cursor()
	cursor.execute(full_query)
	db_ret_value = cursor.fetchall()
	#print db_ret_value
	for every in db_ret_value:
		q_val = every[0]
		split_val = every[1].split(',')
		question_name.append(q_val)
		if q_val == 'atten_boysGirl':
			for val in split_val:
				atten_boysGirl.append(val)
		if q_val == 'atten_week':
			for val in split_val:
				atten_week.append(val)
			#funcenter_week = [val for val in split_val]
		if q_val == 'atten_Age16_18':
			for val in split_val:
				atten_Age16_18.append(val)
			#funcenter_attenAge16_17 = [val for val in split_val]
		if q_val == 'atten_Age13_15':
			for val in split_val:
				atten_Age13_15.append(val)
		if q_val == 'atten_Age10_12':
			for val in split_val:
				atten_Age10_12.append(val)
		if q_val == 'atten_Age19_24':
			for val in split_val:
				atten_Age19_24.append(val)
		if q_val == 'atten_Dalit':
			for val in split_val:
				atten_Dalit.append(val)
		if q_val == 'atten_excludeCaste':
			for val in split_val:
				atten_Brahmin.append(val)
		if q_val == 'atten_Janajati':
			for val in split_val:
				atten_Janajati.append(val)
		if q_val == 'atten_Muslim':
			for val in split_val:
				atten_Muslim.append(val)
		if q_val == 'otherEvent_eventsAttendence':
			for val in split_val:
				otherEvent_eventsAttendence.append(val)
		if q_val == 'otherEvent_Male':
			for val in split_val:
				otherEvent_Male.append(val)
		if q_val == 'otherEvent_Female':
			for val in split_val:
				otherEvent_Female.append(val)
	
	#girls group
	girls_table = get_html_table(get_np_table_data("Girls",atten_boysGirl,atten_week,atten_Age16_18,atten_Age13_15,atten_Age10_12,atten_Age19_24,atten_Dalit,atten_Brahmin,atten_Janajati,atten_Muslim),table_headers_girls)
	
	#boys group
	boys_table = get_html_table(get_np_table_data("Boys",atten_boysGirl,atten_week,atten_Age16_18,atten_Age13_15,atten_Age10_12,atten_Age19_24,atten_Dalit,atten_Brahmin,atten_Janajati,atten_Muslim),table_headers_boys)

	#Event_group
	activity_dict = {}
	#print('otherEvent_eventsAttendence::',otherEvent_eventsAttendence)
	for idx in range(0,len(otherEvent_eventsAttendence)):
		event = int(otherEvent_eventsAttendence[idx])
		atten_male = int(otherEvent_Male[idx])
		atten_female = int(otherEvent_Female[idx])
		atten_total = atten_male+atten_female
		male_avg = atten_male/2
		female_avg = atten_female/2
		total_avg = int(male_avg)+int(female_avg)
		
		if activity_dict.has_key(event):
			tmpArr = activity_dict.get(event)
			tmpArr[0] += atten_male
			tmpArr[1] += atten_female
			tmpArr[2] += atten_total
			tmpArr[3] += male_avg
			tmpArr[4] += female_avg
			tmpArr[5] += total_avg
			activity_dict[event] = tmpArr
		else:
			activity_dict[event] = [atten_male,atten_female,atten_total,male_avg,female_avg,total_avg]
	#print('activity_dict::',activity_dict)
	for key in activity_dict:
		data_list_activities[int(key)-1][1] = activity_dict.get(key)[0]
		data_list_activities[int(key)-1][2] = activity_dict.get(key)[1]
		data_list_activities[int(key)-1][3] = activity_dict.get(key)[2]
		data_list_activities[int(key)-1][4] = activity_dict.get(key)[3]
		data_list_activities[int(key)-1][5] = activity_dict.get(key)[4]
		data_list_activities[int(key)-1][6] = activity_dict.get(key)[5]

	activities_table = get_html_table(data_list_activities,table_headers_activities)

	connection.close()
	if request.is_ajax():
		jsonData = {}
		jsonData[str('girls_table')] = girls_table
		jsonData[str('boys_table')] = boys_table
		jsonData[str('activities_table')] = activities_table
		#print jsonData
		return HttpResponse(json.dumps(jsonData),content_type='application/json'); 

	filter_json = get_report_filters_value(request,'np')

	variables = RequestContext(request, {
		'head_title': 'Project Summary',
		'girls_table':girls_table,
		'boys_table':boys_table,
		'activities_table':activities_table,
		'filter_json':filter_json,
		'rpt_type': 'np'
		})
	output = render(request,'attendence_activity_report.html',variables);
	return HttpResponse(output)

def get_report_bd_attendence_activity(request):

	table_headers_girls = ['Girls Group','10-12','13-15','16-17','Total Avg','Hindu','Muslim']
	table_headers_boys = ['Boys Group','10-12','13-15','16-17','Total Avg','Hindu','Muslim']
	table_headers_activities = ['Activities','Male','Female','Total','Male Avg','Female Avg','Total Avg']
	data_list_activities = [
	['Activity with Role Model','0','0','0','0','0','0'],
	['Advocacy-District Level on allocation on services for Adolescent','0','0','0','0','0','0'],
	# ['Arrange Fair','0','0','0','0','0','0'],
	# ['Awareness building by campaign','0','0','0','0','0','0'],
	['Campaign on "Amrao Korchi','0','0','0','0','0','0'],
	['Campaign with fathers on fatherhood in collaboration','0','0','0','0','0','0'],
	['Campaign-Activities-Drama','0','0','0','0','0','0'],
	['Campaign-Activities-Flim Show','0','0','0','0','0','0'],
	['Campaign-Activities-USE of IEC materials','0','0','0','0','0','0'],
	['Community dialogue /Talk Show','0','0','0','0','0','0'],
	['Conduct quarterly sharing meeting','0','0','0','0','0','0'],
	['Coordination meeting (UP,UNO office)','0','0','0','0','0','0'],
	['Create space for potential adolescent girls to use journalist training','0','0','0','0','0','0'],
	['Cross learning visit  among  EVAW Forum members','0','0','0','0','0','0'],
	['Cross learning visit within Fun Centre (boys)','0','0','0','0','0','0'],
	['Cross learning visit within Fun Centre (girls)','0','0','0','0','0','0'],
	['Day observance','0','0','0','0','0','0'],
	['Demonstrate drama','0','0','0','0','0','0'],
	['Ensure birth registration (Age10-17)','0','0','0','0','0','0'],
	['Exit Workshop/meeting at villages & Upazila','0','0','0','0','0','0'],
	['Forum Theatre Show','0','0','0','0','0','0'],
	['Fun Center group leader orientation -boys','0','0','0','0','0','0'],
	['Fun Center group leader orientation-girls','0','0','0','0','0','0'],
	['GED training with CV,CF','0','0','0','0','0','0'],
	['Learning and reflection with adolescents and EVAW Forum members','0','0','0','0','0','0'],
	['Meeting with EVAW Forum and other GO, NGO','0','0','0','0','0','0'],
	['Organize masculinity and sexuality training  (FF,SCM & CV,CF)','0','0','0','0','0','0'],
	['Reflection workshop between EVAW and other local  elite and religious leader.','0','0','0','0','0','0'],
	['Resposive parenting (TBD)','0','0','0','0','0','0'],
	['Session with EVAW Forum','0','0','0','0','0','0'],
	['Session with Fathers Group','0','0','0','0','0','0'],
	['Session with Mothers Group','0','0','0','0','0','0'],
	['Sharing with local NGOs','0','0','0','0','0','0'],
	['Spot Meeting','0','0','0','0','0','0'],
	['Tea Stall meeting','0','0','0','0','0','0'],
	['Workshop for sharing positive practices of marriage registers','0','0','0','0','0','0'],
	['Other','0','0','0','0','0','0']]
	
	
	pngo_name = '%'
	upzilla_name = '%'
	union_name = '%'
	village_name = '%'
	ff_name  = '%'
	start_date ='2016-01-01'
	end_date = datetime.datetime.now().strftime ("%Y-%m-%d")
	if request.is_ajax():
		pngo_name = request.POST.get('pngo')
		upzilla_name = request.POST.get('upzilla')
		union_name = request.POST.get('union')
		village_name = request.POST.get('village')
		ff_name = request.POST.get('ff_name','%')
		start_date = request.POST.get('start_date')
		end_date = request.POST.get('end_date')
		#print 'Ajax calling serve it...'
	question_name = []
	funcenter_boundary_list = []
	funcenter_week =[]
	funcenter_attenAge16_17 = []
	funcenter_attenAge13_15 =[]
	funcenter_attenAge10_12 =[]
	funcenter_attenMuslim = []
	funcenter_attenHindu = []
	otherAct_activities = []
	otherAct_attenMale = []
	otherAct_attenFemale = []
	otherAct_attenTotal = []

	raw_query = "select instance_parse_data.question,instance_parse_data.qvalue_json->>'question_value' as value from instance_parse_data,logger_instance where instance_parse_data.instance_id=logger_instance.id"
	sub_query = " and logger_instance.json->>'geo/pngo'::text like '"+pngo_name+"' and logger_instance.json->>'geo/upazila'::text like '"+upzilla_name+"' and logger_instance.json->>'geo/union'::text like '"+union_name+"' and logger_instance.json->>'geo/village'::text like '"+village_name+"' and logger_instance.json->>'geo/ffName'::text like '%"+ff_name+"%' and (logger_instance.json->>'_submission_time')::timestamp::date between '"+start_date+"' and '"+end_date+"' and (instance_parse_data.question like 'funcenter_boundaryPart' or instance_parse_data.question like 'funcenter_attenAge16_17' or instance_parse_data.question like 'funcenter_attenMuslim' or instance_parse_data.question like 'funcenter_attenAge13_15' or instance_parse_data.question like 'funcenter_attenAge10_12' or instance_parse_data.question like 'funcenter_week' or instance_parse_data.question like 'funcenter_attenHindu' or instance_parse_data.question like 'otherAct_attenFemale' or instance_parse_data.question like 'otherAct_attenMale' or instance_parse_data.question like 'otherAct_attenTotal' or instance_parse_data.question like 'otherAct_activities') "
	full_query = raw_query+sub_query
	#print full_query
	cursor = connection.cursor()
	cursor.execute(full_query)
	db_ret_value = cursor.fetchall()
	#print db_ret_value
	for every in db_ret_value:
		q_val = every[0]
		split_val = every[1].split(',')
		question_name.append(q_val)
		if q_val == 'funcenter_boundaryPart':
			for val in split_val:
				funcenter_boundary_list.append(val)
		if q_val == 'funcenter_week':
			for val in split_val:
				funcenter_week.append(val)
			#funcenter_week = [val for val in split_val]
		if q_val == 'funcenter_attenAge16_17':
			for val in split_val:
				funcenter_attenAge16_17.append(val)
			#funcenter_attenAge16_17 = [val for val in split_val]
		if q_val == 'funcenter_attenAge13_15':
			for val in split_val:
				funcenter_attenAge13_15.append(val)
			#funcenter_attenAge13_15 = [val for val in split_val]
		if q_val == 'funcenter_attenAge10_12':
			for val in split_val:
				funcenter_attenAge10_12.append(val)
			#funcenter_attenAge10_12 = [val for val in split_val]
		if q_val == 'funcenter_attenMuslim':
			for val in split_val:
				funcenter_attenMuslim.append(val)
			#funcenter_attenMuslim = [val for val in split_val]
		if q_val == 'funcenter_attenHindu':
			for val in split_val:
				funcenter_attenHindu.append(val)
			#funcenter_attenHindu = [val for val in split_val]
		if q_val == 'otherAct_activities':
			for val in split_val:
				otherAct_activities.append(val)
		if q_val == 'otherAct_attenMale':
			for val in split_val:
				otherAct_attenMale.append(val)
		if q_val == 'otherAct_attenFemale':
			for val in split_val:
				otherAct_attenFemale.append(val)
		if q_val == 'otherAct_attenTotal':
			for val in split_val:
				otherAct_attenTotal.append(val)
	#girls group
	girls_table = get_html_table(get_bd_table_data("1",funcenter_boundary_list,funcenter_week,funcenter_attenAge16_17,funcenter_attenAge13_15,funcenter_attenAge10_12,funcenter_attenMuslim,funcenter_attenHindu),table_headers_girls)
	
	#boys group
	boys_table = get_html_table(get_bd_table_data("2",funcenter_boundary_list,funcenter_week,funcenter_attenAge16_17,funcenter_attenAge13_15,funcenter_attenAge10_12,funcenter_attenMuslim,funcenter_attenHindu),table_headers_boys)

	#activities_group
	activity_dict = {}
	for idx in range(0,len(otherAct_activities)):
		activity = int(otherAct_activities[idx])
		atten_male = int(otherAct_attenMale[idx])
		atten_female = int(otherAct_attenFemale[idx])
		atten_total = int(otherAct_attenTotal[idx])
		
		male_avg = round(float(atten_male)/35,2)
		female_avg = round(float(atten_female)/35,2)
		total_avg = float(male_avg)+float(female_avg)
		
		if activity_dict.has_key(activity):
			tmpArr = activity_dict.get(activity)
			tmpArr[0] += atten_male
			tmpArr[1] += atten_female
			tmpArr[2] += atten_total
			tmpArr[3] += male_avg
			tmpArr[4] += female_avg
			tmpArr[5] += total_avg
			activity_dict[activity] = tmpArr
		else:
			activity_dict[activity] = [atten_male,atten_female,atten_total,male_avg,female_avg,total_avg]
	
	for key in activity_dict:
		data_list_activities[int(key)-1][1] = activity_dict.get(key)[0]
		data_list_activities[int(key)-1][2] = activity_dict.get(key)[1]
		data_list_activities[int(key)-1][3] = activity_dict.get(key)[2]
		data_list_activities[int(key)-1][4] = activity_dict.get(key)[3]
		data_list_activities[int(key)-1][5] = activity_dict.get(key)[4]
		data_list_activities[int(key)-1][6] = activity_dict.get(key)[5]
	activities_table = get_html_table(data_list_activities,table_headers_activities)

	connection.close()
	if request.is_ajax():
		jsonData = {}
		jsonData[str('girls_table')] = girls_table
		jsonData[str('boys_table')] = boys_table
		jsonData[str('activities_table')] = activities_table
		
		return HttpResponse(json.dumps(jsonData),content_type='application/json'); 

	filter_json = get_report_filters_value(request,'bd')

	variables = RequestContext(request, {
		'head_title': 'Project Summary',
		'girls_table':girls_table,
		'boys_table':boys_table,
		'activities_table':activities_table,
		'filter_json':filter_json,
		'rpt_type': 'bd'
		})
	output = render(request,'attendence_activity_report.html',variables);
	return HttpResponse(output)

def get_np_table_data(data_type,att_boygirl,att_week,att_16_18,att_13_15,att_10_12,att_19_24,att_d,att_b,att_jj,att_m):
	data_list_group = [['week 1 avg',0,0,0,0,0,0,0,0,0],
				['week 2 avg',0,0,0,0,0,0,0,0,0],
				['week 3 avg',0,0,0,0,0,0,0,0,0],
				['week 4 avg',0,0,0,0,0,0,0,0,0],
				['week 5 avg',0,0,0,0,0,0,0,0,0],
				['Avg',0,0,0,0,0,0,0,0,0]]
	week_dict = {}
	indices = [i for i, x in enumerate(att_boygirl) if x == data_type]
	#print 'indices'
	#print indices
	for idx in indices:
		week = att_week[idx]
		attenAge16_17 = int(att_16_18[idx])
		attenAge13_15 = int(att_13_15[idx])
		attenAge10_12 = int(att_10_12[idx])
		attenAge19_24 = int(att_19_24[idx])
		attenDalit = int(att_d[idx])
		attenBrahmin = int(att_b[idx])
		attenJanajati = int(att_jj[idx])
		attenMuslim = int(att_m[idx])
		weekly_avg = (attenAge16_17+attenAge13_15+attenAge10_12+attenAge19_24)/4
		if week_dict.has_key(week):
			data_list = week_dict.get(week)

			data_list[0] += attenAge10_12
			# print 'data_list: '+ 'attenAge10_12'
			# print str(data_list[0]) + ' '+str(attenAge10_12)
			data_list[1] += attenAge13_15
			data_list[2] += attenAge16_17
			data_list[3] += attenAge19_24
			data_list[4] += weekly_avg
			data_list[5] += attenDalit
			data_list[6] += attenBrahmin
			data_list[7] += attenJanajati
			data_list[8] += attenMuslim
			# print 'data_list'+ 'week: '+week
			# print data_list
			week_dict[week] = data_list
		else:
			week_dict[week] = [attenAge10_12,attenAge13_15,attenAge16_17,attenAge19_24,weekly_avg,attenDalit,attenBrahmin,attenJanajati,attenMuslim]

		for week in week_dict.keys():
			data_list_group[int(week)-1][1] = week_dict.get(week)[0]
			data_list_group[int(week)-1][2] = week_dict.get(week)[1]
			data_list_group[int(week)-1][3] = week_dict.get(week)[2]
			data_list_group[int(week)-1][4] = week_dict.get(week)[3]
			data_list_group[int(week)-1][5] = week_dict.get(week)[4]
			data_list_group[int(week)-1][6] = week_dict.get(week)[5]
			data_list_group[int(week)-1][7] = week_dict.get(week)[6]
			data_list_group[int(week)-1][8] = week_dict.get(week)[7]
			data_list_group[int(week)-1][9] = week_dict.get(week)[8]
		
		for index in range(1,10):
			sum_data = 0
			for idx in range(0,5):
				#print data_list_group[idx][index]
				sum_data +=  int(data_list_group[idx][index])
			data_list_group[5][index] = sum_data/5
	return data_list_group

def get_bd_table_data(data_type,f_boundary,f_week,f_att_1617,f_att_1315,f_att_1012,f_att_m,f_att_h):
	data_list_group = [['week 1 avg','0','0','0','0','0','0'],
				['week 2 avg','0','0','0','0','0','0'],
				['week 3 avg','0','0','0','0','0','0'],
				['week 4 avg','0','0','0','0','0','0'],
				['week 5 avg','0','0','0','0','0','0'],
				['Avg','','','','','','']]
	week_dict = {}
	indices = [i for i, x in enumerate(f_boundary) if x == data_type]
	# print 'indices'
	# print indices
	for idx in indices:
		week = f_week[idx]
		attenAge16_17 = int(f_att_1617[idx])
		attenAge13_15 = int(f_att_1315[idx])
		attenAge10_12 = int(f_att_1012[idx])
		try :
		    attenMuslim = int(f_att_m[idx])
		except Exception, e:
		    continue
		weekly_avg = float(attenAge16_17+attenAge13_15+attenAge10_12)/3
		attenHindu = int(f_att_h[idx])
		#attenMuslim = int(f_att_m[idx])
		if week_dict.has_key(week):
			data_list = week_dict.get(week)

			data_list[0] += attenAge10_12
			# print 'data_list: '+ 'attenAge10_12'
			# print str(data_list[0]) + ' '+str(attenAge10_12)
			data_list[1] += attenAge13_15
			data_list[2] += attenAge16_17
			data_list[3] += weekly_avg
			data_list[4] += attenHindu
			data_list[5] += attenMuslim
			# print 'data_list'+ 'week: '+week
			# print data_list
			week_dict[week] = data_list
		else:
			week_dict[week] = [attenAge10_12,attenAge13_15,attenAge16_17,weekly_avg,attenHindu,attenMuslim]

		for week in week_dict.keys():
			data_list_group[int(week)-1][1] = week_dict.get(week)[0]
			data_list_group[int(week)-1][2] = week_dict.get(week)[1]
			data_list_group[int(week)-1][3] = week_dict.get(week)[2]
			data_list_group[int(week)-1][4] = week_dict.get(week)[3]
			data_list_group[int(week)-1][5] = week_dict.get(week)[4]
			data_list_group[int(week)-1][6] = week_dict.get(week)[5]
		
		for index in range(1,7):
			sum_data = 0
			for idx in range(0,5):
				#print data_list_group[idx][index]
				sum_data +=  float(data_list_group[idx][index])
			data_list_group[5][index] = float(sum_data/5)
	return data_list_group

def get_report_bd_girl_boy_status_change(request):
	
	status_list = ['dummy','Unmarried to married','School Re-enrollment','School Dropout','IGA involvement','Others']
	table_headers_stat_change = ['Fun Center Name','Boys/girls Name','Age','Change Status']
	col_width = ['30%','25%','25%','25%']
	data_list_stat_change = []

	pngo_name = '%'
	vdc_name = '%'
	upzilla_name = '%'
	union_name = '%'
	village_name = '%'
	status = '%'
	if request.is_ajax():
		pngo_name = request.POST.get('pngo')
		upzilla_name = request.POST.get('upzilla')
		union_name = request.POST.get('union')
		village_name = request.POST.get('village')
		status = request.POST.get('status')

	main_query = "select instance_parse_data.instance_id,instance_parse_data.question,instance_parse_data.qvalue_json->>'question_value' as value from instance_parse_data where instance_parse_data.form_id_string like 'bd_boys_girls_profile' and instance_parse_data.instance_id"
	sub_query = " in (select logger_instance.id from logger_instance where logger_instance.json->>'profile/pngo' like '"+pngo_name+"'  and logger_instance.json->>'profile/upazila' like '"+upzilla_name+"' and logger_instance.json->>'profile/union' like '"+union_name+"' and logger_instance.json->>'profile/village' like '"+village_name+"' and  logger_instance.json->>'profile/changeStatus' like '%"+status+"%' ) and (instance_parse_data.question like 'profile_village' or instance_parse_data.question like 'profile_adoName' or instance_parse_data.question like 'profile_age' or instance_parse_data.question like 'profile_changeStatus') order by instance_id"

	full_query = main_query + sub_query
	# print full_query
	cursor = connection.cursor()
	cursor.execute(full_query)
	db_ret_value = cursor.fetchall()
	# print db_ret_value
	inst_id = 0
	count = 0
	data_list = [0,0,0,0]
	# print 'db_ret_value'
	# print db_ret_value
	for each in db_ret_value:
		g_b_age = 0
		g_b_Name = ''
		g_b_fun_center = ''
		g_b_status = ''
		
		if each[1] == 'profile_village':
			data_list[0] = str(each[2])
			count += 1
		if each[1] == 'profile_adoName':
			data_list[1] = str(each[2])
			count += 1
		if each[1] == 'profile_age':
			data_list[2] = int(each[2])
			count += 1
		if each[1] == 'profile_changeStatus':
			# print each[2]
			stat_changed = ''
			stat_list = str(each[2]).split(' ')
			for every in stat_list:				
				stat_changed = stat_changed + '\n' + status_list [int(every)] + ','
			data_list[3] = stat_changed
			# data_list[3] = status_list[ int(each[2]) ]
			count += 1
		if count == 4:
			data_list_stat_change.append(data_list)
			data_list = [0,0,0,0]
			count = 0
	
	chng_stat_table = get_html_table(data_list_stat_change,table_headers_stat_change,col_width)
	results = None
	try:
		cursor.execute("BEGIN")
		#get_care_bd_g_b_stat_chart_data
		cursor.callproc("get_care_bd_g_b_stat_chart_data2", [pngo_name, upzilla_name, union_name, village_name, status])
		results = cursor.fetchall()
		cursor.execute("COMMIT")
	except Exception as e:
		print e
		connection._rollback()
	finally:
		cursor.close()

	status_chart_data = {}
	if results is not None:
		for every in results:
			if str(every[0]) == '1':
				status_chart_data['unm_to_marr'] = int(every[1])
			if str(every[0]) == '2':
				status_chart_data['s_re_enrol'] = int(every[1])
			if str(every[0]) == '3':
				status_chart_data['sch_drop'] = int(every[1])
			if str(every[0]) == '4':
				status_chart_data['iga_inv'] = int(every[1])
			if str(every[0]) == '5':
				status_chart_data['oth'] = int(every[1])
			
	# status_chart_data['unm_to_marr'] = int(results[0])
	# status_chart_data['s_re_enrol'] = int(results[1])
	# status_chart_data['sch_drop'] = int(results[2])
	# status_chart_data['iga_inv'] = int(results[3])
	# status_chart_data['oth'] = int(results[4])
	
	# print status_chart_data

	if request.is_ajax():
		jsonData = {}
		jsonData[str('chng_stat_table')] = chng_stat_table
		jsonData[str('status_chart_data')] = status_chart_data	
		jsonData[str('rpt_type')] = 'bd'		
		return HttpResponse(json.dumps(jsonData),content_type='application/json');
	filter_json = get_report_filters_value(request,'bd')
	variables = RequestContext(request, {
		'head_title': 'Project Summary',
		'chng_stat_table':chng_stat_table,
		'status_chart_data':status_chart_data,
		'filter_json':filter_json,
		'rpt_type': 'bd',
		})
	output = render(request,'g_b_status_change_report.html',variables);
	return HttpResponse(output)

def get_report_np_girl_boy_status_change(request):

	status_list = ['dummy','Unmarried To Married','Out of School to In School','In School to dropout','Not Gouna to Gouna','Others']

	table_headers_stat_change = ['Fun Center Name','Boys/girls Name','Age','Change Status']

	col_width = ['30%','25%','15%','35%']
	data_list_stat_change = []

	pngo_name = '%'
	vdc_name = '%'
	gender = '%'
	status = '%'
	start_date = '2016-01-01'
	end_date = datetime.datetime.now().strftime ("%Y-%m-%d")

	if request.is_ajax():
		pngo_name = request.POST.get('pngo')
		vdc_name = request.POST.get('vdc')
		gender = request.POST.get('gender')
		status = request.POST.get('status')
		start_date = request.POST.get('start_date')
		end_date = request.POST.get('end_date')

	try:
		cursor = connection.cursor()
		cursor.execute("BEGIN")
		cursor.callproc("get_care_np_g_b_stat_data", [pngo_name, vdc_name, gender, status,start_date,end_date])
		db_ret_value = cursor.fetchall()
		cursor.execute("COMMIT")
	finally:
		cursor.close()


	inst_id = 0
	count = 0
	data_list = [0,0,0,0]
	# print 'db_ret_value'
	# print db_ret_value
	for each in db_ret_value:
		g_b_age = 0
		g_b_Name = ''
		g_b_fun_center = ''
		g_b_status = ''
		
		if each[1] == 'profile_vdc':
			data_list[0] = str(each[2])
			count += 1
		if each[1] == 'detail_adoName':
			data_list[1] = str(each[2])
			count += 1
		if each[1] == 'detail_age':
			data_list[2] = int(each[2])
			count += 1
		if each[1] == 'detail_statusChange':
			data_list[3] = status_list[ int(each[2]) ]
			count += 1
		if count == 4:
			data_list_stat_change.append(data_list)
			data_list = [0,0,0,0]
			count = 0
	# print data_list_stat_change

	chng_stat_table = get_html_table(data_list_stat_change,table_headers_stat_change,col_width)

	try:
		cursor = connection.cursor()
		cursor.execute("BEGIN")
		cursor.callproc("get_care_np_g_b_stat_chart_data", [pngo_name,vdc_name, gender,status,start_date,end_date])
		results = cursor.fetchone()
		cursor.execute("COMMIT")
	finally:
		cursor.close()
	# print results
	status_chart_data = {}
	status_chart_data['unm_to_marr'] = int(results[0])
	status_chart_data['out_sch_in_sch'] = int(results[1])
	status_chart_data['in_sch_dout'] = int(results[2])
	status_chart_data['not_gou_to_gou'] = int(results[3])
	status_chart_data['oth'] = int(results[4])
	# status_chart_data['dth_in_law'] = int(results[5])
	list_other_data = []
	try:
		cursor = connection.cursor()
		cursor.execute("BEGIN")
		cursor.callproc("get_care_np_g_b_stat_chart_data_others", [pngo_name,vdc_name, gender,status,start_date,end_date])
		tuple_other_data = cursor.fetchall()
		cursor.execute("COMMIT")
	finally:
		cursor.close()
	for other_data in tuple_other_data:
		list_other_data.append(str(other_data[0]))
		
	status_chart_data['oth_type'] = list_other_data

	if request.is_ajax():
		jsonData = {}
		jsonData[str('chng_stat_table')] = chng_stat_table
		jsonData[str('status_chart_data')] = status_chart_data
		jsonData[str('rpt_type')] = 'np'			
		return HttpResponse(json.dumps(jsonData),content_type='application/json');

	filter_json = get_report_filters_value(request,'np')

	variables = RequestContext(request, {
		'chng_stat_table':chng_stat_table,
		'status_chart_data':status_chart_data,
		'filter_json':filter_json,
		'rpt_type': 'np',
		})
	output = render(request,'g_b_status_change_report.html',variables);
	return HttpResponse(output)

def get_report_bd_staff_transformation(request):
	table_headers_staff_trans = ['ID','Month','Fun Center Name','CF','CV','Details']
	col_width = ['20%','20%','20%','20%','20%']
	
	data_list_staff_trans = []

	pngo_name = '%'
	vdc_name = '%'
	upzilla_name = '%'
	union_name = '%'
	village_name = '%'
	start_date = '2016-01-01'
	end_date = datetime.datetime.now().strftime ("%Y-%m-%d")

	if request.is_ajax():
		pngo_name = request.POST.get('pngo')
		upzilla_name = request.POST.get('upzilla')
		union_name = request.POST.get('union')
		village_name = request.POST.get('village')
		start_date = request.POST.get('start_date')
		end_date = request.POST.get('end_date')
		
		
	cursor = connection.cursor()
	try:
		cursor.execute("BEGIN")
		cursor.callproc("get_care_bd_staff_trans_data", [pngo_name, upzilla_name, union_name, village_name, start_date,end_date])
		results = cursor.fetchall()
		row_count = cursor.rowcount
		cursor.execute("COMMIT")
	finally:
		cursor.close()
	
	curr_inst_id = 0
	count = 0
	tb_data_list = None
	tb_data_dict = {}
	row_data_dict = None

	for each in results:
		row_count-=1
		if (curr_inst_id != int(each[0])):
			if row_data_dict is not None:
				tb_data_dict[str(curr_inst_id)] = row_data_dict
			if tb_data_list is not None:
				tb_data_list[0] = count
				btn_html = '<button class="btn" id="'+str(curr_inst_id)+'" type="button" onclick="">Details</button>'
				tb_data_list[5] = btn_html
				data_list_staff_trans.append(tb_data_list)
			curr_inst_id = int(each[0])
			tb_data_list = [None,None,None,None,None,None]
			row_data_dict={}
			count+=1
		if row_count == 0:
			if row_data_dict is not None:
				tb_data_dict[str(curr_inst_id)] = row_data_dict
			if tb_data_list is not None:
				tb_data_list[0] = count
				btn_html = '<button class="btn" id="'+str(curr_inst_id)+'" type="button" onclick="pop_details()">Details</button>'
				tb_data_list[5] = btn_html
				data_list_staff_trans.append(tb_data_list)

		#print each
		if(each[1] == 'cfChanges'):
			row_data_dict['cfChanges'] = str(each[2].encode('utf-8'))
		if(each[1] == 'cvTransformation'):
			row_data_dict['cvTransformation'] = str(each[2])
			tb_data_list[4] = 'yes' if int(each[2]) == 1 else 'No'
		if(each[1] == 'cvChanges'):
			row_data_dict['cvChanges'] = str(each[2].encode('utf-8'))
		if(each[1] == 'cfTransformation'):
			row_data_dict['cfTransformation'] = str(each[2])
			tb_data_list[3] = 'yes' if int(each[2]) == 1 else 'No'
		if(each[1] == 'geo_village'):
			row_data_dict['geo_village'] = str(each[2])
			tb_data_list[2] = str(each[2])
		if(each[1] == 'geo_month'):
			row_data_dict['geo_month'] = str(each[2])
			tb_data_list[1] = str(each[2])

	
	staff_trans_table = get_html_table(data_list_staff_trans,table_headers_staff_trans,col_width)

	cursor = connection.cursor()
	try:
		cursor.execute("BEGIN")
		cursor.callproc("get_care_bd_staff_trans_chart_data", [pngo_name, upzilla_name, union_name, village_name, start_date,end_date])
		chart_db_value = cursor.fetchone()
		cursor.execute("COMMIT")
	finally:
		cursor.close()
	
	# print chart_db_value
	trans_chart_data = {}
	trans_chart_data['cf_yes'] = int(chart_db_value[0])
	trans_chart_data['cf_no'] = int(chart_db_value[1])
	trans_chart_data['cv_yes'] = int(chart_db_value[2])
	trans_chart_data['cv_no'] = int(chart_db_value[3])

	if request.is_ajax():
		jsonData = {}
		jsonData[str('staff_trans_table')] = staff_trans_table
		jsonData[str('trans_chart_data')] = trans_chart_data
		jsonData[str('tb_data_dict')] = tb_data_dict			
		return HttpResponse(json.dumps(jsonData),content_type='application/json');
	filter_json = get_report_filters_value(request,'bd')
	variables = RequestContext(request, {
		'staff_trans_table': staff_trans_table,
		'trans_chart_data': trans_chart_data,
		'tb_data_dict':tb_data_dict,
		'filter_json': filter_json,
		'rpt_type': 'bd',
		})
	output = render(request,'staff_transformation_report.html',variables);
	return HttpResponse(output)

def get_report_bd_obsrv_jrnal(request):

	pngo_name = '%'
	vdc_name = '%'
	upzilla_name = '%'
	union_name = '%'
	village_name = '%'
	start_date = '2016-01-01'
	end_date = datetime.datetime.now().strftime ("%Y-%m-%d")
	filter_json = get_report_filters_value(request,'bd')

	if request.is_ajax():
		pngo_name = request.POST.get('pngo')
		upzilla_name = request.POST.get('upzilla')
		union_name = request.POST.get('union')
		village_name = request.POST.get('village')
		start_date = request.POST.get('start_date')
		end_date = request.POST.get('end_date')
		# print pngo_name
	cursor = connection.cursor()
	try:
		cursor.execute("BEGIN")
		cursor.callproc("get_care_bd_ff_obsrv_data", [pngo_name, upzilla_name, union_name, village_name, start_date,end_date])
		db_return = cursor.fetchall()
		row_count = cursor.rowcount
		cursor.execute("COMMIT")
	finally:
		cursor.close()
	# print db_return
	# final data creation array
	chng_bound_part_name = ['dummy','girls','boys','mothers','fathers','role_m','evw_forum','cv','cf','other']
	chng_bound_part_count = [0,0,0,0,0,0,0,0,0,0]
	chng_exp_unexp_count = [0,0,0]
	chng_major_minor_count = [0,0,0,0]
	chng_pos_neg_count = [0,0,0]
	# end of final data creation array

	chng_bound_part = []
	chng_exp_unexp = []
	chng_major_minor = []
	chng_pos_neg = []
	chng_union = []
	chng_village = []
	
	for each_row in db_return:
		ques_name = str(each_row[1])
		if ques_name == 'change_boundaryPart':
			chng_bound_part.append(int(each_row[2]))
		if ques_name == 'change_ExpectUnexpect':
			chng_exp_unexp.append(int(each_row[2]))
		if ques_name == 'change_MajorMinor':
			chng_major_minor.append(int(each_row[2]))	
		if ques_name == 'change_PositiveNegative':
			chng_pos_neg.append(int(each_row[2]))
		if ques_name == 'change_union':
			chng_union.append(str(each_row[2]))
		if ques_name == 'change_village':
			chng_village.append(str(each_row[2]))

	data_to_send = {}


	if union_name != '%':
		
		tmp_chng_exp_unexp = []
		tmp_chng_major_minor = []
		tmp_chng_pos_neg = []
		
		for idx in range(len(chng_bound_part)):
			chng_bound_part_count[chng_bound_part[idx]] += 1
		indices = [i for i, x in enumerate(chng_union) if x == union_name]
		
		for idx in indices:
			tmp_chng_exp_unexp.append(chng_exp_unexp[idx])
			tmp_chng_major_minor.append(chng_major_minor[idx])
			tmp_chng_pos_neg.append(chng_pos_neg[idx])
		data_to_send = __get_bd_obsrv_data_dict(tmp_chng_major_minor,tmp_chng_pos_neg,tmp_chng_exp_unexp,chng_bound_part)

	else:
		data_to_send = __get_bd_obsrv_data_dict(chng_major_minor,chng_pos_neg,chng_exp_unexp,chng_bound_part)
	
	if request.is_ajax():
		jsonData = {}
		jsonData[str('data_dict')] = data_to_send			
		return HttpResponse(json.dumps(jsonData),content_type='application/json');

	variables = RequestContext(request, {
		'rpt_type': 'bd',
		'filter_json': filter_json,
		'data_dict': json.dumps(data_to_send),
		})
	output = render(request,'obsrv_journal_report.html',variables);
	return HttpResponse(output)

def __get_bd_obsrv_data_dict(chng_major_minor,chng_pos_neg,chng_exp_unexp,chng_bound_part):

	chng_bound_part_name = ['dummy','girls','boys','mothers','fathers','role_m','evw_forum','cv','cf','other']
	data_dict = {}
	chng_bound_part_count = [0,0,0,0,0,0,0,0,0,0]
	chng_exp_unexp_count = [0,0,0]
	chng_pos_neg_count = [0,0,0]
	pos_exp_unexp = [0,0]
	neg_exp_unexp = [0,0]

	for idx in range(len(chng_bound_part)):
		chng_bound_part_count[chng_bound_part[idx]] += 1

	indices_major = [i for i, x in enumerate(chng_major_minor) if x == 1]
	indices_minor = [i for i, x in enumerate(chng_major_minor) if x == 2]
	indices_imp = [i for i, x in enumerate(chng_major_minor) if x == 3]
	
	for each in indices_major:

		chng_pos_neg_count[chng_pos_neg[each]] += 1
		if chng_pos_neg[each] == 1:
			pos_exp_unexp[chng_exp_unexp[each]-1] +=1
		else:
			neg_exp_unexp[ chng_exp_unexp[each]-1 ] +=1 
		# chng_exp_unexp_count[chng_exp_unexp[each]] += 1
	else:
		data_dict['major_chng_total'] = len(indices_major)
		data_dict['major_pos_neg'] = chng_pos_neg_count
		data_dict['major_pos_exp_unexp'] = pos_exp_unexp
		data_dict['major_neg_exp_unexp'] = neg_exp_unexp 

	chng_exp_unexp_count = [0,0,0]
	chng_pos_neg_count = [0,0,0]
	pos_exp_unexp = [0,0]
	neg_exp_unexp = [0,0]

	for each in indices_minor:
		chng_pos_neg_count[chng_pos_neg[each]] += 1
		if chng_pos_neg[each] == 1:
			pos_exp_unexp[chng_exp_unexp[each]-1] +=1
		else:
			neg_exp_unexp[ chng_exp_unexp[each]-1 ] +=1 
	else:
		data_dict['minor_chng_total'] = len(indices_minor)
		data_dict['minor_pos_neg'] = chng_pos_neg_count
		data_dict['minor_pos_exp_unexp'] = pos_exp_unexp
		data_dict['minor_neg_exp_unexp'] = neg_exp_unexp 

	chng_exp_unexp_count = [0,0,0]
	chng_pos_neg_count = [0,0,0]
	pos_exp_unexp = [0,0]
	neg_exp_unexp = [0,0]

	for each in indices_imp:
		chng_pos_neg_count[chng_pos_neg[each]] += 1
		if chng_pos_neg[each] == 1:
			pos_exp_unexp[chng_exp_unexp[each]-1] +=1
		else:
			neg_exp_unexp[ chng_exp_unexp[each]-1 ] +=1 
	else:
		data_dict['imp_chng_total'] = len(indices_imp)
		data_dict['imp_pos_neg'] = chng_pos_neg_count
		data_dict['imp_pos_exp_unexp'] = pos_exp_unexp
		data_dict['imp_neg_exp_unexp'] = neg_exp_unexp 
	
	for i in range(len(chng_bound_part_name)):
		data_dict[chng_bound_part_name[i]] = chng_bound_part_count[i]

	return data_dict

def get_html_table(data_list,table_headers=None,column_width=None):
    if column_width is None:
    	htmlcode = HTML.table(data_list,header_row=table_headers ,col_width=['20%','15%', '15%', '15%', '15%', '15%', '20%'])
    else:
    	htmlcode = HTML.table(data_list,header_row=table_headers ,col_width=column_width)
    return_html = str(htmlcode).replace('<TABLE', '<TABLE class="table table-bordered" id="sortable"')
    return return_html

def get_report_filters_value(request,rpt_type):
	
	if rpt_type =='bd':
		asd_union_village_dict = {}
		asd_upzilla_union_dict = {}
		pngo_upzilla_dict = {}
	
		#ASD
		bhatipara_village_list = ['Dattagram','Dhalkutub','Kuchir gaon','Mothurapur']
		chamarchar_village_list = ['Chamarchar','Kamalpur','Kartikpur','Lowlarchar','Perua','Shamarchar']
		deraisaromangal_village_list = ['Chitolia','Chondipur','Nachni','Saromangal']
		jogdol_village_list = ['Kambribij','Nurpur','Sarongpasha']
		kulanj_village_list = ['Dokshin Suriar Par','Tetoya','Uttar Suriarpar']
		rofinagar_village_list = ['Khagaura','Mirjapur','Sechni']
		tarol_village_list = ['Amirpur','Bawshi','Islampur','Kadirpur','Vhangador']
		

		
		asd_union_village_dict['Bhatipara'] = bhatipara_village_list
		asd_union_village_dict['Chamarchar'] = chamarchar_village_list
		asd_union_village_dict['Derai Saromangal'] = deraisaromangal_village_list
		asd_union_village_dict['Jogdol'] = jogdol_village_list
		asd_union_village_dict['Kulanj'] = kulanj_village_list
		asd_union_village_dict['Rofinagar'] = rofinagar_village_list
		asd_union_village_dict['Tarol'] = tarol_village_list

		asd_upzilla_union_dict['Derai'] = asd_union_village_dict



		asd_union_village_dict = {}

		dohalia_village_list = ['Hazi Nagar menda','Noagaon','Panail','Shibpur']
		mannargaon_village_list = ['Aminpur','Karimpur','Mannargoan','Rampur']
		pandargaon_village_list = ['Gopi Nogor','Notun Krishnonagor','Polirchar','Sonapur']

		asd_union_village_dict['Dohalia'] = dohalia_village_list
		asd_union_village_dict['Mannargaon'] = mannargaon_village_list
		asd_union_village_dict['Pandargaon'] = pandargaon_village_list

		asd_upzilla_union_dict['Doarabazar'] = asd_union_village_dict
		pngo_upzilla_dict['ASD'] = asd_upzilla_union_dict
		
		#END OF ASD
		

		#JASHIS
		
		beheli_village_list = ['Bagani','Bahali Alipur','Gopalpur','Gossho Gram','Horinagar','Islampur','Notun Moshalgat','Putia','Shibpur']
		fenarback_village_list = ['Posim Fenarbak','Sarifpur','Dokkin Laxmipur','Enatnagar','Josmontopur','Krisnopur','Saydnogor','Shukdebpur','Uttar LaxmiPur']
		jamalganj_sadar_village_list = ['Batal Alipur','Chanpur -2','Golerhati','Hinhu Kalipur','Insanpur','Junupur','KaminiPur','Masumpur','NoyaHalot','Sharthpur','Vuhyer hati']
		sachnabazar_village_list = ['Akthapara','Bramongaun','Chanpur -1','Fazilpur','Horipur','Kanda goan','Kukraporshi','Mofij Nogor','Polockpur','Polok','Radanager','Shorifpur']
		vimkhali_village_list = ['Chandar Nagar','Fekulmahamudpur','Gazipur','Hararkandi','KalKatkha','Kamlabaz','Mollikpur','Teranagor','Vanda']


		#jashis_union_village_dict = {}
		jashis_upzilla_union_dict = {}
		

		

		jashis_union_village_dict = {}

		jashis_union_village_dict['Beheli'] = beheli_village_list
		jashis_union_village_dict['Fenarback'] = fenarback_village_list
		jashis_union_village_dict['Jamalgonj Sadar'] = jamalganj_sadar_village_list
		jashis_union_village_dict['Sachnabazar'] = sachnabazar_village_list
		jashis_union_village_dict['Vimkhali'] = vimkhali_village_list

		jashis_upzilla_union_dict['Jamalganj'] = jashis_union_village_dict
		

		pngo_upzilla_dict['JASHIS'] = jashis_upzilla_union_dict
		
		return json.dumps(pngo_upzilla_dict)
	if rpt_type =='np':
		pngo_vdc_dict ={}
		dsdc_vdc_list = [ 'Baluhawa','Ajigara','Bashkhor','Gotihawa','Harnampur','Pursottampur','Sihokhor','Somdih' ]
		sss_vdc_list = ['Bairghat','Chhotkiramnagar','Ekala','Maryadpur','Raypur','Semara','Tenuhawa','Thu. Piprahawa']
		pngo_vdc_dict['DSDC'] = dsdc_vdc_list
		pngo_vdc_dict['SSS'] = sss_vdc_list

		return json.dumps(pngo_vdc_dict)
	return 0


def get_report_pentaho(request):
	variables = RequestContext(request, {
		'head_title': 'Project Summary',
		})
	output = render(request,'test_pentaho_report.html',variables);
	return HttpResponse(output)

	



