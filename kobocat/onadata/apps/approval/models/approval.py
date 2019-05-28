from django.contrib.auth.models import User
from django.db import models
from onadata.apps.logger.models.xform import XForm
from onadata.apps.logger.models.instance import Instance
from jsonfield import JSONField


class ApprovalDef(models.Model):
    formid = models.CharField(max_length=200)
    userid = models.CharField(max_length=200)
    approver_label = models.IntegerField(default=0)
    approval_type = models.CharField(max_length=200)
    approver_type = models.CharField(max_length=200)

    class Meta:
        app_label = 'approval'


class ApprovalList(models.Model):
    formid = models.CharField(max_length=200)
    subbmissionid = models.CharField(max_length=200)
    userid = models.CharField(max_length=200)
    status = models.CharField(max_length=200)
    label = models.IntegerField(default=0)
    approval_def = models.ForeignKey(ApprovalDef, related_name='approvalList', null=True)

    class Meta:
        app_label = 'approval'

class InstanceApproval(models.Model):
    formid = models.CharField(max_length=200)
    senderid = models.CharField(max_length=200)
    instance = models.ForeignKey(Instance, related_name='InstanceApproval', null=True)
    json = JSONField(default={}, null=False)
    status = models.CharField(max_length=200, default='New')
    # shows when we first received this instance
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'approval'

