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
from django.db.models import ProtectedError
from django.db import connection
from django.db.models import Max, Sum
import json
from datetime import *
from collections import OrderedDict


# *************************** Utility Functions *****************************************


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


def unicodoToString(tup):
   #if isinstance(str(tup), unicode):
   #    return json.dumps(tup)
   #else:
   #    return tup 
   return json.dumps(tup)
