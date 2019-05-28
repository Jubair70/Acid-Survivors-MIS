from django.db import models


class Schedule(models.Model):
    form_id = models.CharField(max_length=200)
    form_title = models.CharField(max_length=200)
    beneficiary_id = models.CharField(max_length=200,null=True,default='',blank=True)
    user_id = models.CharField(max_length=200)
    instance_id = models.CharField(max_length=200)
    household_id = models.CharField(max_length=200)
    schedule_user = models.CharField(max_length=200)
    schedule_date = models.DateTimeField(auto_now_add=True)
    schedule_status = models.CharField(max_length=200)

    class Meta:
        app_label = 'scheduling'
