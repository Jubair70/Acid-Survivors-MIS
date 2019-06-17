from django.db import models
from django.contrib.auth.models import User

# Create your models here.
from django.db.models import Count

# extra imports 
from onadata.apps.unicef.models import GeoPSU

class UserModuleProfile(models.Model):
    user = models.OneToOneField(User)
    expired = models.DateTimeField()
    # designation = models.CharField(max_length=200)
    # The additional attributes we wish to include.
    admin = models.BooleanField(default=False)
    organisation_name = models.ForeignKey('Organizations', on_delete=models.PROTECT)
    designation = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100)
    date_of_birth = models.CharField(max_length=100)
    gender = models.CharField(max_length=100)
    nid = models.CharField(max_length=100)
    marital_status = models.CharField(max_length=100)

    current_division = models.CharField(max_length=100)
    current_district = models.CharField(max_length=100)
    current_upazila = models.CharField(max_length=100)
    current_union = models.CharField(max_length=100)
    current_ward = models.CharField(max_length=100)
    current_address = models.CharField(max_length=100)
    current_postoffice = models.CharField(max_length=100)
    present_permanent_address_same = models.CharField(max_length=100)
    permanent_division = models.CharField(max_length=100)
    permanent_district = models.CharField(max_length=100)
    permanent_upazila = models.CharField(max_length=100)
    permanent_union = models.CharField(max_length=100)
    permanent_ward = models.CharField(max_length=100)
    permanent_address = models.CharField(max_length=100)
    permanent_postoffice = models.CharField(max_length=100)
    joining_date = models.CharField(max_length=100)
    release_date = models.CharField(max_length=100)
    #psu = models.OneToOneField(GeoPSU,related_name='user_psu',on_delete=models.PROTECT)
    
    # Override the __unicode__() method to return out something meaningful!
    def __str__(self):
        return self.user.username

    class Meta:
       app_label = 'usermodule'


class UserPasswordHistory(models.Model):
    user_id = models.IntegerField()
    password = models.CharField(max_length=150)
    # designation = models.CharField(max_length=200)
    date = models.DateTimeField()

    # Override the __unicode__() method to return out something meaningful!
    def __str__(self):
        return self.user


class UserFailedLogin(models.Model):
    user_id = models.IntegerField()
    login_attempt_time= models.DateTimeField(auto_now_add=True)


    def was_username(self):
        current_user= User.objects.get(id=self.user_id)
        return current_user;
    was_username.short_description = 'Username'


class OrganizationDataAccess(models.Model):
    # observer_oraganization = models.CharField(max_length=150)
    # observable_oraganization = models.CharField(max_length=150)
    observer_organization = models.ForeignKey('Organizations',related_name='user_observer_organization', on_delete=models.CASCADE)
    observable_organization = models.ForeignKey('Organizations',related_name='user_observable_organization', on_delete=models.CASCADE)
    

    class Meta:
        unique_together = ('observer_organization', 'observable_organization',)


class Organizations(models.Model):
    organization = models.CharField(max_length=150)
    parent_organization = models.ForeignKey('Organizations',blank=True, null=True,related_name='parent_org', on_delete=models.PROTECT)
    # Override the __unicode__() method to return out something meaningful!
    def __str__(self):
        return self.organization

    class Meta:
       app_label = 'usermodule'


class MenuItem(models.Model):
    title = models.CharField(max_length=150)
    url = models.CharField(max_length=150)
    list_class = models.CharField(max_length=150)
    icon_class = models.CharField(max_length=150)
    parent_menu = models.ForeignKey('MenuItem',blank=True, null=True, on_delete=models.CASCADE)
    sort_order = models.PositiveSmallIntegerField(default=0)
    def __str__(self):
        return self.title

    

# Role + Organization model
class OrganizationRole(models.Model):
    organization = models.ForeignKey('Organizations',related_name='role_organization_name', on_delete=models.CASCADE)
    role = models.CharField(max_length=150)
    
    class Meta:
        unique_together = ('organization', 'role',)

    def __str__(self):
        return self.organization.organization + " => "+ self.role

# Role-Menu Permission Mapping
class MenuRoleMap(models.Model):
    role = models.ForeignKey('OrganizationRole',related_name='model_map_role', on_delete=models.CASCADE)
    menu = models.ForeignKey('MenuItem',related_name='model_map_menu', on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('role', 'menu',)
    
    def __str__(self):
        return self.role

    def __unicode__(self):
        return '%s' % (self.role)


# User-Role Permission Mapping
class UserRoleMap(models.Model):
    user = models.ForeignKey('UserModuleProfile',related_name='usermodule_role', on_delete=models.CASCADE)
    role = models.ForeignKey('OrganizationRole',related_name='map_user_role', on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user','role',)
    
    def __str__(self):
        return self.user        



