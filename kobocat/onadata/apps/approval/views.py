from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.template import RequestContext
from django.views.decorators.http import require_POST
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
from onadata.apps.logger.models.xform import XForm

from onadata.apps.approval.models.approval import ApprovalList
from onadata.apps.logger.models.instance import Instance
from onadata.apps.logger.models.note import Note
from onadata.apps.approval.models.approval import ApprovalDef
from onadata.apps.approval.models.approval import InstanceApproval
import os
import smtplib
from django.conf import settings
from onadata.libs.utils.user_auth import get_xform_and_perms
from onadata.libs.utils.log import audit_log
from onadata.libs.utils.log import Actions
from django.utils.translation import ugettext as _
from onadata.libs.utils.user_auth import has_permission
from django.core.urlresolvers import reverse
from onadata.apps.main.views import show,show_project_settings
import sys

xform_instances = settings.MONGO_DB.instances


def data_approval_list(request):
    form_id = request.POST.get('formid');
    xform = get_object_or_404(XForm, id_string__exact=form_id)
    response_data = {'submission_id': request.POST.get('submissionid'), 'form_id': request.POST.get('formid'),
                     'form_owner': xform.user.username}
    return HttpResponse(json.dumps(response_data), content_type="application/json")


@login_required
def pending_approval(request):
    context = RequestContext(request)
    approvals = ApprovalList.objects.filter(userid=request.user.username, status='Pending')
    print('\n \n getting approval where request.user.username = ' + request.user.username + ' and approval list :')
    context.approvals = approvals
    # return render_to_response("pending-approval.html", context_instance=context)
    return render(request, "pending_approval.html", {'approvals': approvals})


def save_approval_note(notetext, instance_id):
    """

    :param note:
    :param instance_id:
    """
    instance_ = get_object_or_404(Instance, id__exact=instance_id)
    note = Note()
    note.note = notetext
    note.instance = instance_
    note.save()


"""
Approver try to approved data from  user interface of pending approval.
Received parameters are submissionid, formid, note and userid.
Approved data and update and emailed next level approver pending data status if exists, otherwise,
update mongo data base that data is finally approved.
"""


def data_approve(request):
    submissionid = request.POST.get('submissionid')
    userid = request.user.username
    formid = request.POST.get('formid')
    note = request.POST.get('note')

    # data = [{"approve" : ids}]
    print(
        '\n\n approving data where submission id = ' + request.POST.get('submissionid') + ' user_id = ' + userid + '\n')
    # save_approval_note(note, submissionid)
    current_user_approval = ApprovalList.objects.filter(formid=formid, userid=userid,
                                                        subbmissionid=submissionid).first()
    current_user_approval.status = "Approved"
    current_user_approval.save(update_fields=['status'])
    # update mongo db
    xform_instances.update({"_id": int(submissionid)}, {'$set': {"approve": "Processing"}})
    update_instance_approval_status(submissionid, 'Processing')
    approval_count = ApprovalList.objects.filter(formid=formid, subbmissionid=submissionid, label=current_user_approval.label, status="Pending").count()

    if approval_count is None or approval_count == 0:
        print('\n\n approvals are None where approver level = ' + str(
            current_user_approval.approval_def.approver_label) + '\n')
        next_level_approver = ApprovalDef.objects.filter(formid=formid, approver_type='approver',
                                                         approver_label=int(
                                                             current_user_approval.approval_def.approver_label + 1)).count()
	next_approver_label = int(current_user_approval.approval_def.approver_label) + 1;
	#print('\n\tnext_approver_label..= ' + next_approver_label)
        if next_level_approver is not 0:
            update_upcoming_approver_status(formid, submissionid, next_approver_label)
        else:
            print('\n\tdata_approve:Updating mongo and postgres data with approve status...\n')
            # update mongo db that data is finally approved
            xform_instances.update({"_id": int(submissionid)}, {'$set': {"approve": "Approved"}})
            update_instance_approval_status(submissionid, 'Approved')

        send_info_next_notifier(formid, submissionid, current_user_approval.approval_def.approver_label, True)

    else:
        approval_defs = ApprovalDef.objects.filter(formid=formid, approver_label=int(
            current_user_approval.approval_def.approver_label)).distinct()
        if approval_defs is not None:
            print('first level test where approval_def is not none')
            for approval_d in approval_defs:
                if approval_d.approval_type == 'any':
                    print('second level test where approval_type is any')
                    next_approver_label = int(current_user_approval.approval_def.approver_label) + 1;
                    update_upcoming_approver_status(formid, submissionid,next_approver_label)
                    send_info_next_notifier(formid, submissionid, current_user_approval.approval_def.approver_label,
                                            True)
    # xform_instance.remove(9)
    return HttpResponse("You're approving data %s.")

def update_instance_approval_status(submissionid, status):
    _instance = get_object_or_404(Instance, id__exact=submissionid)
    instance_approval = InstanceApproval.objects.filter(instance=_instance).first()
    instance_approval.status = status
    instance_approval.save(update_fields=['status'])

def update_upcoming_approver_status(formid, submissionid,label):
    next_approvals = ApprovalList.objects.filter(formid=formid, subbmissionid=submissionid,label=label,
                                                 status="Upcoming").distinct()
    if next_approvals is not None and len(next_approvals) != 0:
        print('first level test where approval_def is not none')
        for approval in next_approvals:
            approval.status = "Pending"
            approval.save(update_fields=['status'])
    else:
        print('\n\tdata_approve:Updating mongo and postgres data with approve status...2\n')
        update_instance_approval_status(submissionid, 'Approved')
        xform_instances.update({"_id": int(submissionid)}, {'$set': {"approve": "Approved"}})	


"""
Sent email to next level all approver or notifier where approver current status is pending.
"""


def send_info_next_notifier(formid, submissionid, current_user_approval_level, approve):
    next_level_approver = ApprovalDef.objects.filter(formid=formid,
                                                     approver_label=int(current_user_approval_level + 1)).distinct()
    for approval_def in next_level_approver:
        next_notifier = ApprovalList.objects.filter(formid=formid, subbmissionid=submissionid,
                                                    userid=approval_def.userid).first()
        #send_email_to_approver(next_notifier, approval_def.approver_type, approve)


def send_email_to_approver(approver, approver_type, approve):
    print('\n\t send_email_to_approver : approver type: ' + approver_type)
    kobocat_url = os.environ.get('KOBOCAT_URL')
    smtp_url = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
    smtp_port = getattr(settings, 'EMAIL_PORT', 587)
    sender = getattr(settings, 'EMAIL_HOST_USER', 'ratnacse06@gmail.com')
    password = getattr(settings, 'EMAIL_HOST_PASSWORD', 'cmecsrktwwithqml')
    receiver = 'mpower@gmail.com'
    content_user = get_object_or_404(User, username__iexact=approver.userid)
    receiver = content_user.email

    if not kobocat_url.endswith('/'):
        kobocat_url += '/'
    url = kobocat_url + approver.userid + '/forms/' + approver.formid + '/pending_instance/?s_id=' + str(
        approver.subbmissionid) + '#/' + str(approver.subbmissionid)
    msg = MIMEMultipart('alternative')
    text = ''
    html = ''
    if approver_type == 'notify' and approve == True:
        text = "Hi!\nYou have received an approval data \nHere is the link to view approval data:\nhttp://www.python.org"
        html = """\
            <html>
            <head></head>
            <body>
            <p>Hi!<br>
            You have received an Notifying data<br>
            Here is the <a href=" """ + url + """ ">link</a> to view approval data.
            </p>
            </body>
            </html>
            """
    elif approver_type == 'notify' and approve == False:
        print('\n receiver: ' + receiver)

        text = "Hi!\nYour approved data is rejected \nHere is the link to view approval data:\nhttp://www.python.org"
        html = """\
            <html>
            <head></head>
            <body>
            <p>Hi!<br>
            Your approved data is rejected<br>
            Here is the <a href=" """ + url + """ ">link</a> to view approval data.
            </p>
            </body>
            </html>
            """
    elif approver_type == 'approver' and approve == True:
        print('\n\t receiver: ' + receiver)

        text = "Hi!\nYou have received an approval data \nHere is the link to view approval data:\nhttp://www.python.org"
        html = """\
            <html>
            <head></head>
            <body>
            <p>Hi!<br>
            You have received an approval data<br>
            Here is the <a href=" """ + url + """ ">link</a> to view approval data.
            </p>
            </body>
            </html>
            """

    elif approver_type == 'approver' and approve == False:
        print('\n\t receiver: ' + receiver)

        text = "Hi!\nYour approved data is rejected \nHere is the link to view approval data:\nhttp://www.python.org"
        html = """\
            <html>
            <head></head>
            <body>
            <p>Hi!<br>
            Your approved data is rejected<br>
            Here is the <a href=" """ + url + """ ">link</a> to view approval data.
            </p>
            </body>
            </html>
            """

    print ('\n')
    print(html)
    msg['Subject'] = 'The content for data approval'
    msg['From'] = sender
    msg['To'] = receiver

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Send the message via local SMTP server.
    s = smtplib.SMTP(smtp_url, smtp_port)
    # send mail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.

    try:
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(sender, password)
        s.sendmail(sender, receiver, msg.as_string())
        s.quit()
    except smtplib.SMTPServerDisconnected:
        print('Email sending failed, Reason: SMTPServerDisconnected: Connection unexpectedly closed')
    except smtplib.SMTPSenderRefused:
        print('Email sending failed, Reason: SMTPSenderRefused:')
    except smtplib.SMTPException:
        print "Error: unable to send email"


"""
In case of data reject, approver who already approved data have to know about data rejection.
"""


def send_info_previous_user(formid, submissionid, current_user_approval_level, approve):
    print('\n\tsend_info_previous_user formid=' + formid + ' submissionid = ' + submissionid + '\n')
    next_notifies = ApprovalList.objects.filter(formid=formid, subbmissionid=submissionid,
                                                status="Approved").distinct()
    if next_notifies is not None:
        for approval in next_notifies:
            print('\n\tsend_info_previous_user\n' + approval.userid)
            #send_email_to_approver(approval, 'approver', approve)


def data_reject(request):
    submissionid = request.POST.get('submissionid')
    userid = request.user.username
    formid = request.POST.get('formid')

    print(
        '\n\t Reject data where submission id = ' + request.POST.get('submissionid') + ' user_id = ' + userid + '\n')

    current_user_approval = ApprovalList.objects.filter(formid=formid, userid=userid, subbmissionid=submissionid,
                                                        status="Pending").first()
    current_user_approval.status = "Reject"
    current_user_approval.save(update_fields=['status'])
    # update mongo db
    xform_instances.update({"_id": int(submissionid)}, {'$set': {"approve": "Processing"}})
    update_instance_approval_status(submissionid, 'Processing')

    approval_count = ApprovalList.objects.filter(formid=formid, subbmissionid=submissionid, status="Pending").count()

    if approval_count is None or approval_count == 0:
        print('\n\t Reject is None where approver level = ' + str(
            current_user_approval.approval_def.approver_label) + '\n')
        next_level_approver = ApprovalDef.objects.filter(formid=formid, approver_type='approver',
                                                         approver_label=int(
                                                             current_user_approval.approval_def.approver_label + 1)).count()
        if next_level_approver is not 0:
            approval_def = ApprovalDef.objects.filter(formid=formid, approver_label=int(
                current_user_approval.approval_def.approver_label)).first()
            print('\n\t next_level_approver is Exist = \n')
            # When next level approvers are exist and approver_type is any one that case update
            if approval_def.approval_type == 'any':
                next_approver_label = int(current_user_approval.approval_def.approver_label) + 1;
                update_upcoming_approver_status(formid, submissionid)
        else:
            # update mongo db that data is finally rejected
            xform_instances.update({"_id": int(submissionid)}, {'$set': {"approve": "Reject"}})
            update_instance_approval_status(submissionid, 'Reject')
    else:
        approval_defs = ApprovalDef.objects.filter(formid=formid, approver_label=int(
            current_user_approval.approval_def.approver_label)).distinct()
        if approval_defs is not None:
            for approval_d in approval_defs:
                if approval_d.approval_type == 'any':
                    next_approver_label = int(current_user_approval.approval_def.approver_label) + 1;
                    update_upcoming_approver_status(formid, submissionid)
    send_info_previous_user(formid, submissionid, current_user_approval.approval_def.approver_label, False)
    return HttpResponse("You're rejecting data %s.")


"""
Listing logged in user all pending approval data.
"""


def pending_instance(request, username, id_string):
    print('(apps/viewer/views.py) Action: data view from instance controller')
    xform_owner = get_object_or_404(XForm, id_string__exact=id_string)
    xform, is_owner, can_edit, can_view = get_xform_and_perms(
        xform_owner.user.username, id_string, request)
    if request.user.username is not None:
        username = request.user.username
    print(
        '\n\n username : ' + username + '\n form_id: ' + id_string + '\n' + '\n submission_id: ' + request.GET.get(
            's_id', '') + '\n')
    # no access

    if not (xform.shared_data or can_view or
                    request.session.get('public_link') == xform.uuid):
        return HttpResponseForbidden(_(u'Not shared.'))

    audit = {
        "xform": xform.id_string,
    }
    audit_log(
        Actions.FORM_DATA_VIEWED, request.user, xform.user,
        _("Requested instance view for '%(id_string)s'.") %
        {
            'id_string': xform.id_string,
        }, audit, request)

    _id_string = request.GET.get('s_id', '')
    _instance = get_object_or_404(Instance, id__exact=_id_string)
    note_list = Note.objects.filter(instance=_instance).distinct()

    approvals = ApprovalList.objects.filter(userid=username, formid=id_string, subbmissionid=_id_string).first()

    is_approved_or_reject = 'true'
    if approvals is not None:
        is_approved_or_reject = 'false'
        if approvals.status == 'Approved' or approvals.status == 'Reject':
            is_approved_or_reject = 'true'
        elif approvals.status == 'Upcoming' or approvals.status == 'Notify':
            is_approved_or_reject = 'true'

    return render(request, 'pending_instance.html', {
        'username': xform.user.username,
        'id_string': id_string,
        'xform': xform,
        'can_edit': can_edit,
        'note_list': note_list,
        'is_approved_or_reject': is_approved_or_reject
    })


@require_POST
def set_approval(request, username, id_string):
    print("\n\n\n\n\n\n\n setting approval\n\n")
    xform = get_object_or_404(XForm,
                              user__username__iexact=username,
                              id_string__exact=id_string)
    owner = xform.user
    if username != request.user.username \
            and not has_permission(xform, username, request):
        return HttpResponseForbidden(_(u'Permission denied.'))
    try:
        approval = ApprovalDef()
        approval.userid = request.POST['approver']
        approval.formid = id_string
        approval.approver_label = request.POST['label_type']
        approval.approval_type = request.POST['approval_type']
        approval.approver_type = request.POST['approver_type']
        approval_option = request.POST['approval_option']
    except KeyError:
        return HttpResponseBadRequest()

    if approval_option == 'add' and has_no_approval(request, approval, obj=None):
        print(
            "\n Adding new approver where \n userId = " + approval.userid + " \n formid = " + approval.formid + "\n approver_label = " + approval.approver_label + "\n approval_type = " + approval.approval_type + "\n approver_type = " + approval.approver_type)
        user = User.objects.get(username=approval.userid)
        if user.has_perm('change_xform', xform):
            approval.save()
            messages.success(request, '<i class="fa fa-check-circle"></i> New Approver has been set successfully!',
                             extra_tags='alert-success crop-both-side')
        else:
            print('User has not form edit permission...')

    elif approval_option == 'remove':
        approval_list = ApprovalDef.objects.filter(userid=approval.userid, formid=approval.formid)
        for approve in approval_list:
            approve.delete()
            messages.success(request, '<i class="fa fa-check-circle"></i> Approver has been removed successfully!',
                             extra_tags='alert-success crop-both-side')

    return HttpResponseRedirect(reverse(show_project_settings, kwargs={
        'username': username,
        'id_string': id_string
    }))


"""
add only those user has no approval permission for selected form
"""


def has_no_approval(self, approval, obj=None):
    # approvalline = Approveline.objects.raw('SELECT COUNT(*) FROM models_approveline WHERE userid = %s and formid = %s', [approval.userid, approval.formid])
    approval_def = ApprovalDef.objects.filter(userid=approval.userid, formid=approval.formid)
    if approval_def is not None and approval_def.count() > 0:
        return False
    else:
        return True
