from onadata.apps.scheduling.models import Schedule

import json
from django.db import connection
from collections import namedtuple
from django.http import HttpResponse
from onadata.apps.logger.models.xform import XForm


def create_user_schedule(username, instance, beneficiary_id, form_id):
    # getting XForm title depending on received form_id
    form_title = get_xform_title(form_id)

    print('\n\n\n\n\n\n creating schedule... where form_id = ')
    print(form_id)
    print('\n form_title')
    print(form_title)
    print('\n\n\n\n\n')

    # Creating Household Registration based field worker schedule
    schedule = Schedule()
    schedule.beneficiary_id = beneficiary_id
    schedule.household_id = instance.json.get('HH_Id')
    schedule.form_id = form_id
    schedule.form_title = form_title
    schedule.user_id = username
    schedule.instance_id = instance.id
    schedule.schedule_user = username
    schedule.schedule_status = 'Active'
    schedule.save()


def get_xform_title(form_id):
    xform = XForm.objects.filter(id_string=form_id).first()
    if xform is not None:
        return xform.title
    else:
        return form_id + ' form is not uploaded'


def update_schedule_status(schedule_id):
    print('\n\n\n\n\n\n updating schedule status... where schedule id = ')
    print schedule_id
    schedule = None
    try:
        schedule = Schedule.objects.get(id=schedule_id, schedule_status='Active')
    except Schedule.DoesNotExist:
        print('\n \t Schedule not exist...')

    if schedule is not None:
        schedule.schedule_status = 'Done'
        schedule.save()


def submit_user_schedule(request):
    from onadata.apps.scheduling.models import Beneficiary
    
    username = request.GET.get('userId', '')

    schedule_all = Schedule.objects.filter(schedule_user=username, schedule_status='Active').distinct()
    schedule_list = []
    if schedule_all is not None and len(schedule_all) > 0:
        for schedule in schedule_all:
            beneficiary = Beneficiary.objects.filter(beneficiary_id = schedule.beneficiary_id).first()
            head_man = Beneficiary.objects.filter(household_id = schedule.household_id, head_member = True).first()
            response_object = response(schedule, beneficiary, head_man.beneficiary_name)
            schedule_list.append(response_object)

    # schedules = serializers.serialize("json", Schedule.objects.filter(scheduleUser=username, scheduleStatus='Active'),ensure_ascii=False)
    # schedules = serializers.serialize("json", scheduleList, ensure_ascii=False)
    return HttpResponse(json.dumps(schedule_list), content_type="application/json")


def response(schedule, beneficiary,head_man_name):
    beneficiary_name = ''

    form_title = 'Form is not uploaded'
    if beneficiary is not None:
        beneficiary_name = beneficiary.beneficiary_name

    if(schedule.form_title is not None):
        form_title = schedule.form_title
    return {
        'formid': schedule.form_id,
        'formname':form_title,
        'beneficiaryid': schedule.beneficiary_id,
        'householdid': schedule.household_id,
        'id': schedule.id,
        'beneficiaryname': beneficiary_name,
        'anotherMember': head_man_name
    }


# noinspection PyTypeChecker
def my_custom_sql(b_id, h_id):
    cursor = connection.cursor()
    sqlStr = "SELECT beneficiary_id,beneficiary_name,(SELECT beneficiary_name FROM scheduling_beneficiary WHERE household_id =" + h_id + " and head_member = true)as head_man_name FROM scheduling_beneficiary WHERE beneficiary_id = '" + b_id + "'"

    print('\n\n\n\n\n\n Getting sqlStr information .. where sqlStr = ')
    print(sqlStr)

    cursor.execute(sqlStr)

    row = named_tuple_fetch_all(cursor)
    cursor.close()
    print('\n\n\n\n\n\n Getting beneficiary information .. where b_id = ')
    print(b_id)
    print(row)

    return row


def named_tuple_fetch_all(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


def dict_fetch_all(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
        ]


