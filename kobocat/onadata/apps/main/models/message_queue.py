from django.db import models

class Message_Queue(models.Model):
    subscribeid = models.CharField(max_length=255, blank=True)
    status = models.IntegerField(default=0)
    response = models.CharField(max_length=255, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    msg_type = models.IntegerField(default=0)
    class Meta:
        app_label = 'main'