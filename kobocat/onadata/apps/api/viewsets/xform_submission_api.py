import re
import StringIO
import sys
import json
from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from django.http import HttpResponse

from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.authentication import (
    BasicAuthentication,
    TokenAuthentication)
from rest_framework.response import Response
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer

from onadata.apps.logger.models import Instance
from onadata.apps.main.models.user_profile import UserProfile
from onadata.libs import filters
from onadata.libs.authentication import DigestAuthentication
from onadata.libs.mixins.openrosa_headers_mixin import OpenRosaHeadersMixin
from onadata.libs.renderers.renderers import TemplateXMLRenderer
from onadata.libs.serializers.data_serializer import SubmissionSerializer
from onadata.libs.utils.logger_tools import dict2xform, safe_create_instance
from rest_framework import authentication
import logging
from django.contrib.auth import authenticate
from onadata.libs.tasks import instance_parse
from onadata.libs.utils.export_tools import query_mongo
from onadata.apps.viewer.tasks import create_async_export, create_db_async_export

from onadata.apps.scheduling.schedule_utils import create_user_schedule, update_schedule_status
from onadata.apps.scheduling.models.beneficiary_info import insert_beneficiary_info

from onadata.apps.approval.views import update_instance_approval_status
from collections import OrderedDict
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import sys

# 10,000,000 bytes
DEFAULT_CONTENT_LENGTH = getattr(settings, 'DEFAULT_CONTENT_LENGTH', 10000000)
xml_error_re = re.compile('>(.*)<')


def is_json(request):
    return 'application/json' in request.content_type.lower()


def dict_lists2strings(d):
    """Convert lists in a dict to joined strings.

    :param d: The dict to convert.
    :returns: The converted dict."""
    for k, v in d.items():
        if isinstance(v, list) and all([isinstance(e, basestring) for e in v]):
            d[k] = ' '.join(v)
        elif isinstance(v, dict):
            d[k] = dict_lists2strings(v)

    return d


def create_instance_from_xml(username, request):
    xml_file_list = request.FILES.pop('xml_submission_file', [])
    xml_file = xml_file_list[0] if len(xml_file_list) else None
    media_files = request.FILES.values()

    return safe_create_instance(username, xml_file, media_files, None, request)


def create_instance_from_json(username, request):
    request.accepted_renderer = JSONRenderer()
    request.accepted_media_type = JSONRenderer.media_type
    dict_form = request.DATA
    submission = dict_form.get('submission')

    if submission is None:
        # return an error
        return [_(u"No submission key provided."), None]

    # convert lists in submission dict to joined strings
    submission_joined = dict_lists2strings(submission)
    xml_string = dict2xform(submission_joined, dict_form.get('id'))

    xml_file = StringIO.StringIO(xml_string)

    return safe_create_instance(username, xml_file, [], None, request)



class XFormSubmissionApi(OpenRosaHeadersMixin,
                         mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
Implements OpenRosa Api [FormSubmissionAPI](\
    https://bitbucket.org/javarosa/javarosa/wiki/FormSubmissionAPI)

## Submit an XML XForm submission

<pre class="prettyprint">
<b>POST</b> /api/v1/submissions</pre>
> Example
>
>       curl -X POST -F xml_submission_file=@/path/to/submission.xml \
https://example.com/api/v1/submissions

## Submit an JSON XForm submission

<pre class="prettyprint">
<b>POST</b> /api/v1/submissions</pre>
> Example
>
>       curl -X POST -d '{"id": "[form ID]", "submission": [the JSON]} \
http://localhost:8000/api/v1/submissions -u user:pass -H "Content-Type: \
application/json"

Here is some example JSON, it would replace `[the JSON]` above:
>       {
>           "transport": {
>               "available_transportation_types_to_referral_facility": \
["ambulance", "bicycle"],
>               "loop_over_transport_types_frequency": {
>                   "ambulance": {
>                       "frequency_to_referral_facility": "daily"
>                   },
>                   "bicycle": {
>                       "frequency_to_referral_facility": "weekly"
>                   },
>                   "boat_canoe": null,
>                   "bus": null,
>                   "donkey_mule_cart": null,
>                   "keke_pepe": null,
>                   "lorry": null,
>                   "motorbike": null,
>                   "taxi": null,
>                   "other": null
>               }
>           }
>           "meta": {
>               "instanceID": "uuid:f3d8dc65-91a6-4d0f-9e97-802128083390"
>           }
>       }
"""
    authentication_classes = (DigestAuthentication,
                              BasicAuthentication,
                              TokenAuthentication)
    filter_backends = (filters.AnonDjangoObjectPermissionFilter,)
    model = Instance
    permission_classes = (permissions.AllowAny,)
    renderer_classes = (TemplateXMLRenderer,
                        JSONRenderer,
                        BrowsableAPIRenderer)
    serializer_class = SubmissionSerializer
    template_name = 'submission.xml'
    print("before create *******************************")


    def send_option(self, request, *args, **kwargs):
        print("inside options *******************************")
        # if request.method.upper() == 'HEAD':
        access_control_headers = request.META['HTTP_ACCESS_CONTROL_REQUEST_HEADERS'];
        response = HttpResponse(200)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST"
        response["Access-Control-Allow-Headers"] = access_control_headers
        response["Access-Control-Allow-Credentials"] = False
        return response

    def dictfetchall(self,cursor):
        desc = cursor.description
        return [
            OrderedDict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()]

    def __db_fetch_values_dict(self,query):
        cursor = connection.cursor()
        cursor.execute(query)
        fetchVal = self.dictfetchall(cursor)
        cursor.close()
        return fetchVal


    def get_form_attribute(self,request, *args, **kwargs):
        print("inside get_form_attribute *********")
        data = json.loads(request.body)
        form_id = data['id']
        url = data['url']
        username = data['username']
        # form_id = request.GET.get('id')
        # url = request.GET.get('url')
        # username = request.GET.get('username')
        submission_url = "http://" + url + "/" + username + "/submission"
        try:
            qry = "select json::json,uuid,id_string from logger_xform where id =" + str(form_id)
            data = self.__db_fetch_values_dict(qry)[0]
            data['submission_url'] = submission_url
            response = HttpResponse(json.dumps(data))
            response ["Access-Control-Allow-Origin"]= "*"
            return response

        except Exception as e:
            print(e)
            return HttpResponse(status=404)

    def create(self, request, *args, **kwargs):
        print("CREATE@@@@@@@@@@@@@@@@@@@")
        username = self.kwargs.get('username')
        password = self.request.GET.get('password')
        if self.request.user.is_anonymous():
            if username is None and password is None:
                # raises a permission denied exception, forces authentication
                self.permission_denied(self.request)
            else:
                user = get_object_or_404(User, username=username.lower())

                profile, created = UserProfile.objects.get_or_create(user=user)

                if profile.require_auth:
                    # raises a permission denied exception,
                    # forces authentication
                    self.permission_denied(self.request)
        elif not username:
            # get the username from the user if not set
            username = (request.user and request.user.username)

        if request.method.upper() == 'HEAD':
            return Response(status=status.HTTP_204_NO_CONTENT,
                            headers=self.get_openrosa_headers(request),
                            template_name=self.template_name)

        is_json_request = is_json(request)

        error, instance = (create_instance_from_json if is_json_request else
                           create_instance_from_xml)(username, request)

        if error or not instance:
            return self.error_response(error, is_json_request, request)

        # print('instance.xform.id_string')
        # print(instance.xform.id_string)
        # print('\n\n\n\n\n')

        ret_msg = ''
        # creating schedule for current submission
        # if instance.xform.id_string == "household_information":
        #    ret_msg = insert_beneficiary_info(username, instance)
        # create_user_schedule(username, instance)
        # else:
        #   dict_form = request.DATA
        #   schedule_id = dict_form.get("scheduleId");
        #   if schedule_id is not None:
        #       update_schedule_status(schedule_id)

        if ret_msg is not None and len(ret_msg) > 0:
            return self.mobile_user_response(instance, ret_msg, request)

        context = self.get_serializer_context()
        serializer = SubmissionSerializer(instance, context=context)
        instance_parse()  # After new db parse implement stop it

        query_dict = {'_id': str(instance.id)}
        options = {
            'group_delimiter': '/',
            'split_select_multiples': True,
            'binary_select_multiples': False,
            # 'meta': meta.replace(",", "") if meta else None,
            'exp_data_typ': 'lbl'
        }

        if instance.xform.db_export:
            # print 'Entered'
            create_db_async_export(instance.xform, 'dbtable', json.dumps(query_dict), False, options)

        update_instance_approval_status(instance.id, 'Submitted')

        response = Response(serializer.data,
                            headers=self.get_openrosa_headers(request),
                            status=status.HTTP_201_CREATED,
                            template_name=self.template_name)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    def mobile_user_response(self, instance, message, request):
        final_msg = {
            'message': _("Successful submission." + message),
            'formid': instance.xform.id_string,
            'encrypted': instance.xform.encrypted,
            'instanceID': u'uuid:%s' % instance.uuid,
            'submissionDate': instance.date_created.isoformat(),
            'markedAsCompleteDate': instance.date_modified.isoformat()
        }
        return Response(final_msg,
                        headers=self.get_openrosa_headers(request),
                        status=status.HTTP_201_CREATED,
                        template_name=self.template_name)

    def error_response(self, error, is_json_request, request):
        print("Error&&&&&&&&&&&&&&&&")
        if not error:
            error_msg = _(u"Unable to create submission.")
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(error, basestring):
            error_msg = error
            status_code = status.HTTP_400_BAD_REQUEST
        elif not is_json_request:
            return error
        else:
            error_msg = xml_error_re.search(error.content).groups()[0]
            status_code = error.status_code

        return Response({'error': error_msg},
                        headers=self.get_openrosa_headers(request),
                        status=status_code)
