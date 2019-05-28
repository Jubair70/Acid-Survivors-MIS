import simplejson
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Count, Q
from django.http import (HttpResponseRedirect, HttpResponse)
from django.shortcuts import render_to_response, get_object_or_404, render
from django.forms.formsets import formset_factory
from onadata.apps.hhmodule.forms import HouseholdForm, HhMemberForm, SlaForm,SlaNonBeneficiaryForm,SlaMeetingForm
from django.db.models import ProtectedError
from django.db import connection
from django.db.models import Max, Sum
from onadata.apps.hhmodule.models import *
import json
from datetime import *
from django.forms.models import inlineformset_factory
from collections import OrderedDict
from django.forms.formsets import BaseFormSet

from dateutil.relativedelta import relativedelta


# *************************** Build Dashboard *****************************************

def build_dashboard_index(request):
    print "Hello!!"
    context = {
    }
    return render(request, 'hhmodule/build_dashboard.html', context)




'''
utility function for running raw queries
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

