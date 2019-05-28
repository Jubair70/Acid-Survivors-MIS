from django.db import models
from django.contrib.auth.models import User
#from __future__ import unicode_literals
from datetime import *
# Create your models here.


# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Remove `managed = False` lines if you wish to allow Django to create and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.


#************Household Module Models Start***************

from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class DashboardNavigationBar(models.Model):
    #id = models.BigIntegerField(primary_key=True)
    link_name = models.CharField(max_length=150, blank=True)
    parent_link = models.ForeignKey('self', blank=True, null=True)
    order = models.IntegerField()

    def __str__(self):
        return str(self.link_name)
    class Meta:
        managed = False
        db_table = 'dashboard_navigation_bar'

@python_2_unicode_compatible
class DashboardGenerator(models.Model):
    #id = models.IntegerField(primary_key=True)
    tab = models.IntegerField(blank=True, null=True)
    content_type = models.IntegerField(blank=True, null=True)
    html_code = models.TextField(blank=True)
    post_url = models.CharField(max_length=150, blank=True)
    chart_object = models.CharField(max_length=500, blank=True)
    js_code = models.TextField(blank=True)
    filtering = models.CharField(max_length=250, blank=True)
    element_id = models.CharField(max_length=150, blank=True)
    navigation_bar=models.ForeignKey(DashboardNavigationBar)
    datasource_type = models.CharField(max_length=50, blank=True)
    datasource=models.TextField(blank=True)
    chart_type = models.ForeignKey('DashboardChartType', blank=True, null=True)
    content_order = models.IntegerField(blank=True, null=True)
    datasource_manipulator_func= models.CharField(max_length=500, blank=True)
    def __str__(self):
        return str(self.element_id)

    class Meta:
        managed = False
        db_table = 'dashboard_generator'





class DashboardChartType(models.Model):
    #id = models.IntegerField()
    name = models.CharField(max_length=150, blank=True)
    actual_type_name = models.CharField(max_length=150, blank=True)
    function_name = models.CharField(max_length=100, blank=True)
    class Meta:
        managed = False
        db_table = 'dashboard_chart_type'



@python_2_unicode_compatible
class DashboardControlsGenerator(models.Model):
    #id = models.BigIntegerField(primary_key=True)
    control_label = models.CharField(max_length=150, blank=True)
    control_id = models.CharField(max_length=150, blank=True)
    control_name = models.CharField(max_length=150, blank=True)
    control_type = models.CharField(max_length=150, blank=True)
    appearance = models.CharField(max_length=1000, blank=True)
    validation = models.CharField(max_length=150, blank=True)
    filtering = models.CharField(max_length=150, blank=True)
    datasource_type = models.CharField(max_length=150, blank=True)
    datasource = models.CharField(max_length=1000, blank=True)
    #ds_queryset = models.CharField(max_length=150, blank=True)
    #ds_url = models.CharField(max_length=150, blank=True)
    navigation_bar = models.ForeignKey('DashboardNavigationBar', blank=True, null=True)
    cascaded_by=models.ForeignKey('self', blank=True, null=True)
    allignment=models.CharField(max_length=50, blank=True)
    element_order = models.IntegerField()
    def __str__(self):
        return str(self.control_label)

    class Meta:
        managed = False
        db_table = 'dashboard_controls_generator'



class DashboardLoader(models.Model):
    #id = models.BigIntegerField(primary_key=True)
    html_code = models.TextField(blank=True)
    js_code = models.TextField(blank=True)
    name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(default=datetime.now(),blank=True)
    class Meta:
        managed = False
        db_table = 'dashboard_loader'
