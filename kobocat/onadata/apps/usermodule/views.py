from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Count,Q
from django.http import (
    HttpResponseRedirect, HttpResponse)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext,loader
from django.contrib.auth.models import User
from datetime import date, timedelta, datetime
# from django.utils import simplejson
import json
import thread
import threading
import logging
import sys
from django.core.urlresolvers import reverse
import time
import csv
# Create your views here.
from django.db import (IntegrityError,transaction)
from django.db.models import ProtectedError
from django.shortcuts import redirect
from onadata.apps.main.models.user_profile import UserProfile
from onadata.apps.usermodule.forms import UserForm, UserProfileForm, ChangePasswordForm, UserEditForm,OrganizationForm,OrganizationDataAccessForm,ResetPasswordForm
from onadata.apps.usermodule.models import UserModuleProfile, UserPasswordHistory, UserFailedLogin,Organizations,OrganizationDataAccess

from django.contrib.auth.decorators import login_required, user_passes_test
from django import forms
# Menu imports
from onadata.apps.usermodule.forms import MenuForm
from onadata.apps.usermodule.models import MenuItem
# Unicef Imports
from onadata.apps.logger.models import Instance,XForm
# Organization Roles Import
from onadata.apps.usermodule.models import OrganizationRole,MenuRoleMap,UserRoleMap
from onadata.apps.usermodule.forms import OrganizationRoleForm,RoleMenuMapForm,UserRoleMapForm,UserRoleMapfForm
from django.forms.models import inlineformset_factory,modelformset_factory
from django.forms.formsets import formset_factory

from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.shortcuts import render
import pandas
from collections import OrderedDict
import os
from django.core.files.storage import FileSystemStorage
from datetime import date, timedelta, datetime


def __db_commit_query(query):
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    cursor.close()

def admin_check(user):
    current_user = UserModuleProfile.objects.filter(user=user)
    if current_user:
        current_user = current_user[0]
    else:
        return True    
    return current_user.admin


@login_required
def index(request):
    current_user = request.user
    user = UserModuleProfile.objects.filter(user_id=current_user.id)
    admin = False
    if user:
        admin = user[0].admin
    if current_user.is_superuser:
        users = UserModuleProfile.objects.all().order_by("user__username")
        admin = True
        # json_posts = json.dumps(list(users.values('id','user__username' ,'organisation_name__organization','user__email')))
    elif admin:
        org_id_list = get_organization_by_user(request.user)
        users = UserModuleProfile.objects.filter(organisation_name__in=org_id_list).order_by("user__username")
        # json_posts = json.dumps(list(users))
        admin = True
    else:
        users = user
        admin = False
    template = loader.get_template('usermodule/index.html')
    context = RequestContext(request, {
            'users': users,
            'admin': admin,
            # 'json_posts' : json_posts
        })
    return HttpResponse(template.render(context))


@login_required
@user_passes_test(admin_check,login_url='/')
def register(request):
    # Like before, get the request's context.
    context = RequestContext(request)
    admin_check = UserModuleProfile.objects.filter(user=request.user)

    if request.user.is_superuser:
        admin_check = True
    elif admin_check:
        admin_check = admin_check[0].admin
    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False
    
    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST,admin_check=admin_check)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            
            form_bool = request.POST.get("admin", "xxx")
            if form_bool == "xxx":
                form_bool_value = False
            else:
                form_bool_value = True
            
            #encrypted password is saved so that it can be saved in password history table
            encrypted_password = make_password(user.password)
            user.password = encrypted_password
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            # profile.organisation_name = request.POST.get("organisation_name", "-1")
            profile.user = user
            expiry_months_delta = 3
            # Date representing the next expiry date
            next_expiry_date = (datetime.today() + timedelta(expiry_months_delta*365/12))
            profile.expired = next_expiry_date
            profile.admin = form_bool_value
            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            # if 'picture' in request.FILES:
            #     profile.picture = request.FILES['picture']

            # Now we save the UserProfile model instance.
            profile.save()

            # kobo main/models/UserProfile
            main_user_profile = UserProfile(user = user)
            main_user_profile.save()

            # Update our variable to tell the template registration was successful.
            registered = True

            #insert password into password history
            passwordHistory = UserPasswordHistory(user_id = user.id,date = datetime.now())
            passwordHistory.password = encrypted_password
            passwordHistory.save()
            messages.success(request, '<i class="fa fa-check-circle"></i> New User has been registered successfully!',
                             extra_tags='alert-success crop-both-side')
            return HttpResponseRedirect('/usermodule/')

        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print user_form.errors, profile_form.errors
            # profile_form = UserProfileForm(admin_check=admin_check)

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        # get request users org and the orgs he can see then pass it to model choice field
        org_id_list = get_organization_by_user(request.user)
        # org id list is not available for superuser's like kobo
        if not org_id_list:
            UserProfileForm.base_fields['organisation_name'] = forms.ModelChoiceField(queryset=Organizations.objects.all(),empty_label="Select a Organization")
        else:
            UserProfileForm.base_fields['organisation_name'] = forms.ModelChoiceField(queryset=Organizations.objects.filter(pk__in=org_id_list)
,empty_label="Select a Organization")
        profile_form = UserProfileForm(admin_check=admin_check)
        print(profile_form)

    # Render the template depending on the context.
    return render_to_response(
            'usermodule/register.html',
            {'user_form': user_form, 'profile_form': profile_form, 'registered': registered},
            context)


def get_organization_by_user(user):
    org_id_list = []
    current_user = UserModuleProfile.objects.filter(user_id=user.id)
    if current_user:
        current_user = current_user[0]
        all_organizations = get_recursive_organization_children(current_user.organisation_name,[])
        org_id_list = [org.pk for org in all_organizations]
    return org_id_list


# must pass an empty organization_list initally otherwise produces bug.
def get_recursive_organization_children(organization,organization_list=[]):
    organization_list.append(organization)
    observables = Organizations.objects.filter(parent_organization = organization)
    for org in observables:
        if org not in organization_list:
            organization_list = list((set(get_recursive_organization_children(org,organization_list))))
    return list(set(organization_list))


@login_required
@user_passes_test(admin_check,login_url='/')
def organization_index(request):
    context = RequestContext(request)
    all_organizations = []
    if request.user.is_superuser:
        all_organizations = Organizations.objects.all()
    else:
        current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
        if current_user:
            current_user = current_user[0]
        all_organizations = get_recursive_organization_children(current_user.organisation_name,[])
        all_organizations.remove(current_user.organisation_name)
    message = ""
    alert = ""
    org_del_message = request.GET.get('org_del_message')
    org_del_message2 = request.GET.get('org_del_message2')
    return render_to_response(
            'usermodule/organization_list.html',
            {'all_organizations':all_organizations,"message":message,"alert":alert,
            'org_del_message':org_del_message,'org_del_message2':org_del_message2,
            },
            context)

from onadata.apps.usermodule.helpers import COUNTRIES

@login_required
@user_passes_test(admin_check,login_url='/')
def add_organization(request):
    # Like before, get the request's context.
    context = RequestContext(request)
    all_organizations = []
    if request.user.is_superuser:
        all_organizations = Organizations.objects.all()
        OrganizationForm.base_fields['parent_organization'] = forms.ModelChoiceField(queryset=all_organizations,empty_label="Select a Organization",required=False)
    else:
        current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
        if current_user:
            current_user = current_user[0]
        all_organizations = get_recursive_organization_children(current_user.organisation_name,[])
        org_id_list = [org.pk for org in all_organizations]
        # org_id_list = list(set(org_id_list))
        OrganizationForm.base_fields['parent_organization'] = forms.ModelChoiceField(queryset=Organizations.objects.filter(pk__in=org_id_list),empty_label="Select a Parent Organization")
    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    is_added_organization = False
    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        organization_form = OrganizationForm(data=request.POST)
        if organization_form.is_valid():
            obj = organization_form.save()
            org_tbl_id = obj.pk
            org_id = request.POST.get('org_id')
            org_type = request.POST.get('org_type')
            contact_person = request.POST.get('contact_person')
            present_address = request.POST.get('present_address')
            designation = request.POST.get('designation')
            district = request.POST.get('district')
            country = request.POST.get('country')
            date_of_establish = request.POST.get('date_of_establish')
            telephone = request.POST.get('telephone')
            email = request.POST.get('email')
            insert_qry = "INSERT INTO public.org_additional_info (org_id, org_type, contact_person, designation, date_of_establish, present_address, district, country, telephone, email, org_tbl_id) VALUES('"+str(org_id)+"', '"+str(org_type)+"', '"+str(contact_person)+"', '"+str(designation)+"', '"+str(date_of_establish)+"', '"+str(present_address)+"', '"+str(district)+"', '"+str(country)+"', '"+str(telephone)+"', '"+str(email)+"', '"+str(org_tbl_id)+"')"
            __db_commit_query(insert_qry)
            is_added_organization = True
            messages.success(request, '<i class="fa fa-check-circle"></i> New Organization has been added successfully!',
                             extra_tags='alert-success crop-both-side')
            return HttpResponseRedirect('/usermodule/organizations/')
        else:
            print organization_form.errors
            return render_to_response(
            'usermodule/add_organization.html',
            {'all_organizations':all_organizations,'organization_form': organization_form,'is_added_organization': is_added_organization},
            context)
    else:
        organization_form =  OrganizationForm()
        district_fetch_qry = "select id,field_name from geo_data where field_type_id = 86"
        df = pandas.read_sql(district_fetch_qry, connection)
        districts = zip(df.id.tolist(), df.field_name.tolist())
    # Render the template depending on the context.
        return render_to_response(
            'usermodule/add_organization.html',
            {'COUNTRIES':COUNTRIES,'districts':districts,'all_organizations':all_organizations,'organization_form': organization_form,'is_added_organization': is_added_organization},
            context)


@login_required
@user_passes_test(admin_check,login_url='/')
def edit_organization(request,org_id):
    context = RequestContext(request)
    edited = False
    organization = get_object_or_404(Organizations, id=org_id)
    all_organizations = []
    if request.user.is_superuser:
        all_organizations = Organizations.objects.filter(~Q(id = organization.pk))
        OrganizationForm.base_fields['parent_organization'] = forms.ModelChoiceField(queryset=all_organizations,empty_label="Select a Organization",required=False)
    else:
        current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
        if current_user:
            current_user = current_user[0]
        all_organizations = get_recursive_organization_children(current_user.organisation_name,[])
        org_id_list = [org.pk for org in all_organizations]
        org_id_list.remove(organization.pk)
        OrganizationForm.base_fields['parent_organization'] = forms.ModelChoiceField(queryset=Organizations.objects.filter(pk__in=org_id_list),empty_label="Select a Parent Organization")
    
    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        organization_form = OrganizationForm(data=request.POST,instance=organization)
        if organization_form.is_valid():
            organization_form.save()
            user_given_org_id = request.POST.get('org_id')
            org_type = request.POST.get('org_type')
            contact_person = request.POST.get('contact_person')
            present_address = request.POST.get('present_address')
            designation = request.POST.get('designation')
            district = request.POST.get('district')
            country = request.POST.get('country')
            date_of_establish = request.POST.get('date_of_establish')
            telephone = request.POST.get('telephone')
            email = request.POST.get('email')
            update_qry = "UPDATE public.org_additional_info SET org_id='"+str(user_given_org_id)+"', org_type='"+str(org_type)+"', contact_person='"+str(contact_person)+"', designation='"+str(designation)+"', date_of_establish='"+str(date_of_establish)+"', present_address='"+str(present_address)+"', district='"+str(district)+"', country='"+str(country)+"', telephone='"+str(telephone)+"', email='"+str(email)+"' WHERE id="+str(org_id)
            __db_commit_query(update_qry)
            edited = True
            messages.success(request,
                             '<i class="fa fa-check-circle"></i> Organization has been updated successfully!',
                             extra_tags='alert-success crop-both-side')
            return HttpResponseRedirect('/usermodule/organizations/')
        else:
            print organization_form.errors
            return render_to_response(
            'usermodule/edit_organization.html',
            {'org_id':org_id,'organization_form': organization_form, 'edited': edited},
            context)
        # Not a HTTP POST, so we render our form using two ModelForm instances.
        # These forms will be blank, ready for user input.
    else:
        organization_form = OrganizationForm(instance=organization)
        qry = "select * from org_additional_info where org_tbl_id::bigint ="+str(org_id)
        df = pandas.read_sql(qry,connection)
        user_given_org_id = df.org_id.tolist()[0]
        org_type = df.org_type.tolist()[0]
        contact_person = df.contact_person.tolist()[0]
        present_address = df.present_address.tolist()[0]
        designation = df.designation.tolist()[0]
        district = df.district.tolist()[0]
        country = df.country.tolist()[0]
        date_of_establish = df.date_of_establish.tolist()[0]
        telephone = df.telephone.tolist()[0]
        email = df.email.tolist()[0]

        district_fetch_qry = "select id,field_name from geo_data where field_type_id = 86"
        df = pandas.read_sql(district_fetch_qry, connection)
        districts = zip(df.id.tolist(), df.field_name.tolist())

    return render_to_response(
            'usermodule/edit_organization.html',
            {'COUNTRIES':COUNTRIES,'org_id':org_id,'organization_form': organization_form, 'edited': edited,
             'user_given_org_id':user_given_org_id,
             'org_type':org_type,
             'contact_person':contact_person,
             'present_address':present_address,
             'designation':designation,
             'district':district,
             'country':country,
             'date_of_establish':date_of_establish,
             'telephone':telephone,
             'email':email,
             'districts':districts
             },
            context)


@login_required
@user_passes_test(admin_check,login_url='/')
def delete_organization(request,org_id):
    context = RequestContext(request)
    org = Organizations.objects.get(pk = org_id)
    try:
        org.delete()
        del_qry = "delete from org_additional_info where org_tbl_id::bigint = "+str(org_id)
        __db_commit_query(del_qry)
        messages.success(request,
                         '<i class="fa fa-check-circle"></i> Organization has been deleted successfully!',
                         extra_tags='alert-success crop-both-side')
    except ProtectedError:
        org_del_message = """User(s) are assigned to this organization,
        please delete those users or assign them a different organization
        before deleting this organization"""

        org_del_message2 = """Or, This Organization may be parent of 
        one or more organization(s), Change their parent to some other organization."""
        
        return HttpResponseRedirect('/usermodule/organizations/?org_del_message='+org_del_message+"&org_del_message2="+org_del_message2)
    return HttpResponseRedirect('/usermodule/organizations/')


# @login_required
# @user_passes_test(lambda u: u.is_superuser,login_url='/')
# def organization_mapping(request):
#     # Like before, get the request's context.
#     context = RequestContext(request)
#     mapped_organizations = OrganizationDataAccess.objects.all()
#     all_organizations = Organizations.objects.all()
#     has_added_mapping = False

#     # If it's a HTTP POST, we're interested in processing form data.
#     if request.method == 'POST':
#         organization_data_access_form = OrganizationDataAccessForm(data=request.POST)
#         # If the two forms are valid...
#         if organization_data_access_form.is_valid():
#             try:
#                 organization_access_map = organization_data_access_form.save();
#                 organization_access_map.observer_oraganization = request.POST.get("observer_oraganization", "-1")
#                 organization_access_map.observable_oraganization = request.POST.get("observable_oraganization", "-1")
#                 organization_access_map.save()
#                 has_added_mapping = True
#             except IntegrityError as e:
#                 transaction.rollback()
#                 message = "That entry already exists"                
#                 return render_to_response(
#             'usermodule/add_organization_access.html',
#             {'mapped_organizations':mapped_organizations,'all_organizations':all_organizations,"message":message,
#             'organization_data_access_form': organization_data_access_form,'has_added_mapping': has_added_mapping},
#             context)
#         else:
#             print organization_data_access_form.errors
#     # Not a HTTP POST, so we render our form using two ModelForm instances.
#     # These forms will be blank, ready for user input.
#     else:
#         organization_data_access_form =  OrganizationDataAccessForm()
    
#     # Render the template depending on the context.
#     return render_to_response(
#             'usermodule/add_organization_access.html',
#             {'mapped_organizations':mapped_organizations,'all_organizations':all_organizations,'organization_data_access_form': organization_data_access_form,'has_added_mapping': has_added_mapping},
#             context)


@login_required
@user_passes_test(admin_check,login_url='/')
def organization_access_list(request):
    param_user_id = request.POST['id']
    response_data = []
    observer = get_object_or_404(Organizations, id=param_user_id)
    all_organizations = get_recursive_organization_children(observer,[])
    for org in all_organizations:
        data = {}
        data["observer"] = observer.organization
        data["observable"] = org.organization
        response_data.append(data)
    return HttpResponse(json.dumps(response_data), content_type="application/json")

 
# @login_required
# @user_passes_test(admin_check,login_url='/')
# def delete_organization_mapping(request,org_id):
#     mappings = OrganizationDataAccess.objects.filter(id = org_id)
#     mappings.delete()
#     return HttpResponseRedirect('/usermodule/organizations/')


# def get_organization_name(organizations,id):
#     for arra in organizations:
#         if int(arra.id) == int(id):
#             return arra.oraganization
#     return None


@login_required
def edit_profile(request,user_id):
	context = RequestContext(request)
	edited = False
	user = get_object_or_404(User, id=user_id)
	profile = get_object_or_404(UserModuleProfile, user_id=user_id)
        admin_check = UserModuleProfile.objects.filter(user=request.user)
        if request.user.is_superuser:
            admin_check = True
        elif admin_check:
            admin_check = admin_check[0].admin
    # If it's a HTTP POST, we're interested in processing form data.
        if request.method == 'POST':
            # Attempt to grab information from the raw form information.
            # Note that we make use of both UserForm and UserProfileForm.
            user_form = UserEditForm(data=request.POST,instance=user,user=request.user)
            profile_form = UserProfileForm(data=request.POST,instance=profile,admin_check=admin_check)
            # If the two forms are valid...
            if user_form.is_valid() and profile_form.is_valid():
                edited_user = user_form.save(commit=False);
                # password_new = request.POST['password']
                # if password_new:
                #     edited_user.set_password(password_new)
                edited_user.save()
                form_bool = request.POST.get("admin", "xxx")
                if form_bool == "xxx":
                    form_bool_value = False
                else:
                    form_bool_value = True
                # Now sort out the UserProfile instance.
                # Since we need to set the user attribute ourselves, we set commit=False.
                # This delays saving the model until we're ready to avoid integrity problems.
                profile = profile_form.save(commit=False)
                # profile.organisation_name = request.POST.get("organisation_name", "-1")
                # profile.admin = request.POST.get("admin", "False")
                profile.user = edited_user
                profile.admin = form_bool_value
                # Did the user provide a profile picture?
                # If so, we need to get it from the input form and put it in the UserProfile model.
                # if 'picture' in request.FILES:
                #     profile.picture = request.FILES['picture']

                # Now we save the UserProfile model instance.
                profile.save()

                # Update our variable to tell the template registration was successful.
                edited = True
                messages.success(request, '<i class="fa fa-check-circle"></i> User profile has been updated successfully!', extra_tags='alert-success crop-both-side')
                return HttpResponseRedirect('/usermodule/')

            # Invalid form or forms - mistakes or something else?
            # Print problems to the terminal.
            # They'll also be shown to the user.
            else:
                # profile_form = UserProfileForm(admin_check=admin_check)
                print user_form.errors, profile_form.errors

        # Not a HTTP POST, so we render our form using two ModelForm instances.
        # These forms will be blank, ready for user input.
        else:
            user_form = UserEditForm(instance=user,user=request.user)
            org_id_list = get_organization_by_user(request.user)
            if not org_id_list:
                UserProfileForm.base_fields['organisation_name'] = forms.ModelChoiceField(queryset=Organizations.objects.all(),empty_label="Select a Organization")
            else:
                UserProfileForm.base_fields['organisation_name'] = forms.ModelChoiceField(queryset=Organizations.objects.filter(pk__in=org_id_list)
    ,empty_label="Select a Organization")
            profile_form = UserProfileForm(instance = profile,admin_check=admin_check)

        return render_to_response(
                'usermodule/edit_user.html',
                {'id':user_id, 'user_form': user_form, 'profile_form': profile_form, 'edited': edited},
                context)


@login_required
@user_passes_test(admin_check,login_url='/')
def delete_user(request,user_id):
    context = RequestContext(request)
    user = User.objects.get(pk = user_id)
    # deletes the user from both user and rango
    user.delete()
    messages.success(request, '<i class="fa fa-check-circle"></i> This user has been deleted successfully!',
                     extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect('/usermodule/')


def change_password(request):
    context = RequestContext(request)
    if request.GET.get('userid'):
        edit_user = get_object_or_404(User, pk = request.GET.get('userid')) 
        logged_in_user = edit_user.username
        change_password_form = ChangePasswordForm(logged_in_user=logged_in_user)
    else:
        change_password_form = ChangePasswordForm()
    # change_password_form = ChangePasswordForm()
    # Take the user back to the homepage.
    if request.method == 'POST':
        # expiry_months_delta: password change after how many months
        expiry_months_delta = 3
        # Date representing the next expiry date
        next_expiry_date = (datetime.today() + timedelta(expiry_months_delta*365/12))

        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        change_password_form = ChangePasswordForm(data=request.POST)
        username = request.POST['username']
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        current_user = authenticate(username=username, password=old_password)
        if change_password_form.is_valid() and current_user is not None:
            """ current user is authenticated and also new password
             is available so change the password and redirect to
             home page with notification to user """
            encrypted_password = make_password(new_password)
            current_user.password = encrypted_password
            current_user.save()

            passwordHistory = UserPasswordHistory(user_id = current_user.id,date = datetime.now())
            passwordHistory.password = encrypted_password
            passwordHistory.save()

            profile = get_object_or_404(UserModuleProfile, user_id=current_user.id)
            profile.expired = next_expiry_date
            profile.save()
            login(request,current_user)
            return HttpResponseRedirect('/usermodule/')
            # else:
                #     return HttpResponse('changed your own password buddy')
                # return HttpResponse( (datetime.now()+ timedelta(days=30)) )
        else:
            return render_to_response(
                    'usermodule/change_password.html',
                    {'change_password_form': change_password_form,'invalid':True},
                    context)

    return render_to_response(
                'usermodule/change_password.html',
                {'change_password_form': change_password_form},
                context)

@login_required
@user_passes_test(admin_check,login_url='/')
def reset_password(request,reset_user_id):
    context = RequestContext(request)
    reset_password_form = ResetPasswordForm()
    reset_user = get_object_or_404(User, pk=reset_user_id)
    reset_user_profile = get_object_or_404(UserModuleProfile,user=reset_user)
    if request.method == 'POST':
        # expiry_months_delta: password change after how many months
        expiry_months_delta = 3
        # Date representing the next expiry date
        next_expiry_date = (datetime.today() + timedelta(expiry_months_delta*365/12))

        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        reset_password_form = ResetPasswordForm(data=request.POST)
        
        if reset_password_form.is_valid() and reset_user is not None:
            """ current user is authenticated and also new password
             is available so change the password and redirect to
             home page with notification to user """
            encrypted_password = make_password(request.POST['new_password'])
            reset_user.password = encrypted_password
            reset_user.save()

            passwordHistory = UserPasswordHistory(user_id = reset_user.id,date = datetime.now())
            passwordHistory.password = encrypted_password
            passwordHistory.save()

            reset_user_profile.expired = next_expiry_date
            reset_user_profile.save()
            messages.success(request, '<i class="fa fa-check-circle"></i> Your password has been updated successfully!',
                             extra_tags='alert-success crop-both-side')
            return HttpResponseRedirect('/usermodule/')
        else:
            return render_to_response(
                    'usermodule/reset_password.html',
                    {'reset_user':reset_user,'reset_password_form': reset_password_form,'invalid':True},
                    context)

    return render_to_response(
                'usermodule/reset_password.html',
                {'reset_password_form': reset_password_form,
                'reset_user':reset_user,'id':reset_user_id,
                },
                context)


def user_login(request):
    # Like before, obtain the context for the user's request.
    context = RequestContext(request)
    logger = logging.getLogger(__name__)
    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        password = request.POST['password']

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # number of login attempts allowed
            max_allowed_attempts = 5
            # count of invalid logins in db
            counter_login_attempts = UserFailedLogin.objects.filter(user_id=user.id).count()
            # check for number of allowed logins if it crosses limit do not login.
            if counter_login_attempts > max_allowed_attempts:
                return HttpResponse("Your account is locked for multiple invalid logins, contact admin to unlock")

            # Is the account active? It could have been disabled.
            if user.is_active:
                if hasattr(user, 'usermoduleprofile'):
                    current_user = user.usermoduleprofile
                    if date.today() > current_user.expired.date():
                        return HttpResponseRedirect('/usermodule/change-password')
                login(request, user)
                UserFailedLogin.objects.filter(user_id=user.id).delete()
                return HttpResponseRedirect(request.POST['redirect_url'])
            else:
                # An inactive account was used - no logging in!
                # return HttpResponse("Your User account is disabled.")
                return error_page(request,"Your User account is disabled")
        else:
            # Bad login details were provided. So we c an't log the user in.
            # try:
            #     attempted_user_id = User.objects.get(username=username).pk
            # except User.DoesNotExist:
            #     return HttpResponse("Invalid login details supplied when login attempted.")
            # UserFailedLogin(user_id = attempted_user_id).save()
            # print "Invalid login details: {0}, {1}".format(username, password)
            # return HttpResponse("Invalid login details supplied.")
            return error_page(request,"Invalid login details supplied")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        if request.GET.get('next'):
            print request.GET.get('next')
            redirect_url = request.GET.get('next')
        else:
            redirect_url = '/'
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render_to_response('usermodule/login.html', {'redirect_url':redirect_url}, context)


@login_required
@user_passes_test(admin_check,login_url='/')
def locked_users(request):
    # Since we know the user is logged in, we can now just log them out.
    current_user = request.user
    users = []
    message = ''
    max_failed_login_attempts = 5

    user = UserModuleProfile.objects.filter(user_id=current_user.id)
    admin = False
    if user:
        admin = user[0].admin

    if current_user.is_superuser or admin:
        failed_logins = UserFailedLogin.objects.all().values('user_id').annotate(total=Count('user_id')).order_by('user_id')
        for f_login in failed_logins:
            if f_login['total'] > max_failed_login_attempts:
                user = UserModuleProfile.objects.filter(user_id=f_login['user_id'])[0]
                users.append(user)
    else:
        return HttpResponseRedirect("/usermodule/")
    if not users:
        message = "All the user accounts are unlocked"

    # Take the user back to the homepage.
    template = loader.get_template('usermodule/locked_users.html')
    context = RequestContext(request, {
            'users': users,
            'message':message
        })
    return HttpResponse(template.render(context))


@login_required
def unlock(request):
    param_user_id = request.POST['id']
    current_user = request.user
    response_data = {}
    
    user = UserModuleProfile.objects.filter(user_id=current_user.id)
    admin = False
    if user:
        admin = user[0].admin

    if current_user.is_superuser or admin:
        UserFailedLogin.objects.filter(user_id=param_user_id).delete()
        response_data['message'] = 'User unlocked'
    else:
        response_data['message'] = 'You are not authorized to unlock'

    return HttpResponse(json.dumps(response_data), content_type="application/json")


@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)
    # Take the user back to the homepage.
    return HttpResponseRedirect('/login/')


# =======================================================================================
@login_required
@user_passes_test(admin_check,login_url='/')
def add_menu(request):
    context = RequestContext(request)
    all_menu = MenuItem.objects.all()
    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    is_added_menu = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        menu_form = MenuForm(data=request.POST)
        # If the two forms are valid...
        if menu_form.is_valid():
            menu =menu_form.save()
            menu.save()
            is_added_menu = True
        else:
            print menu_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
        return HttpResponseRedirect('/usermodule/menu-list/')
    else:
        menu_form = MenuForm()
    
    # Render the template depending on the context.
        return render_to_response(
            'usermodule/add_menu.html',
            {'all_menu':all_menu,'menu_form': menu_form,
            'is_added_menu': is_added_menu},
            context)


@login_required
@user_passes_test(admin_check,login_url='/')
def menu_index(request):
    context = RequestContext(request)
    all_menu = MenuItem.objects.all().order_by("sort_order")
    return render_to_response(
            'usermodule/menu_list.html',
            {'all_menu':all_menu},
            context)


@login_required
@user_passes_test(admin_check,login_url='/')
def edit_menu(request,menu_id):
    context = RequestContext(request)
    edited = False
    menu = get_object_or_404(MenuItem, id=menu_id)
    
    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        menu_form = MenuForm(data=request.POST,instance=menu)
        
        # If the two forms are valid...
        if menu_form.is_valid():
            edited_user = menu_form.save(commit=False);
            edited_user.save()
            edited = True
            return HttpResponseRedirect('/usermodule/menu-list')
        else:
            print menu_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        menu_form = MenuForm(instance=menu)

    return render_to_response(
            'usermodule/edit_menu.html',
            {'id':menu_id, 'menu_form': menu_form,
            'edited': edited},
            context)


@login_required
@user_passes_test(admin_check,login_url='/')
def delete_menu(request,menu_id):
    context = RequestContext(request)
    menu = MenuItem.objects.get(pk = menu_id)
    # deletes the user from both user and rango
    menu.delete()
    return HttpResponseRedirect('/usermodule/menu-list')


# =========================================================
# Roles based on Organization CRUD
@login_required
@user_passes_test(admin_check,login_url='/')
def add_role(request):
    context = RequestContext(request)
    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    is_added_role = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        role_form = OrganizationRoleForm(data=request.POST)
        print role_form
        # If the two forms are valid...
        if role_form.is_valid():
            role_form.save()
            is_added_role = True
        else:
            print role_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
        messages.success(request, '<i class="fa fa-check-circle"></i> New role has been added successfully!',
                         extra_tags='alert-success crop-both-side')
        return HttpResponseRedirect('/usermodule/roles-list/')
    else:
        if request.user.is_superuser:
            OrganizationRoleForm.base_fields['organization'] = forms.ModelChoiceField(queryset=Organizations.objects.all(),empty_label="Select a Organization")
            role_form = OrganizationRoleForm()
        else:
            org_id_list = get_organization_by_user(request.user)
            OrganizationRoleForm.base_fields['organization'] = forms.ModelChoiceField(queryset=Organizations.objects.filter(pk__in=org_id_list),empty_label="Select a Organization")
            role_form = OrganizationRoleForm()
    # Render the template depending on the context.
        return render_to_response(
            'usermodule/add_role.html',
            {'role_form': role_form,
            'is_added_role': is_added_role},
            context)


@login_required
@user_passes_test(admin_check,login_url='/')
def roles_index(request):
    context = RequestContext(request)
    # filter orgs based on logged in user
    if request.user.is_superuser:
        all_roles = OrganizationRole.objects.all().order_by("organization")
    else:
        user = get_object_or_404(UserModuleProfile, user=request.user)
        current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
        if current_user:
            current_user = current_user[0]
        all_organizations = get_recursive_organization_children(current_user.organisation_name, [])
        org_id_list = [org.pk for org in all_organizations]
        all_roles = OrganizationRole.objects.filter(organization__in=org_id_list)
    return render_to_response(
            'usermodule/roles_list.html',
            {'all_roles':all_roles},
            context)


@login_required
@user_passes_test(admin_check, login_url='/')
def edit_role(request, role_id):
    context = RequestContext(request)
    edited = False
    role = get_object_or_404(OrganizationRole, id=role_id)
    if request.method == 'POST':
        role_form = OrganizationRoleForm(data=request.POST,instance=role)
        if role_form.is_valid():
            role_form.save()
            edited = True
            messages.success(request, '<i class="fa fa-check-circle"></i> This role has been edited successfully!',
                             extra_tags='alert-success crop-both-side')
            return HttpResponseRedirect('/usermodule/roles-list')
        else:
            print role_form.errors
    else:
        if request.user.is_superuser:
            OrganizationRoleForm.base_fields['organization'] = forms.ModelChoiceField(queryset=Organizations.objects.all(),empty_label="Select a Organization")
            
        else:
            org_id_list = get_organization_by_user(request.user)
            OrganizationRoleForm.base_fields['organization'] = forms.ModelChoiceField(queryset=Organizations.objects.filter(pk__in=org_id_list),empty_label="Select a Organization")
        role_form = OrganizationRoleForm(instance=role,initial = {'organization': role.organization,'role': role.role })    
        # role_form = OrganizationRoleForm(instance=role)
    return render_to_response(
            'usermodule/edit_role.html',
            {'id':role_id, 'role_form': role_form,
            'edited': edited},
            context)


@login_required
@user_passes_test(admin_check,login_url='/')
def delete_role(request,role_id):
    context = RequestContext(request)
    role = OrganizationRole.objects.get(pk = role_id)
    # deletes the user from both user and rango
    role.delete()
    messages.success(request, '<i class="fa fa-check-circle"></i> This role has been deleted successfully!',
                     extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect('/usermodule/roles-list')


# =========================================================
@login_required
@user_passes_test(admin_check,login_url='/')
def role_menu_map_index(request):
    context = RequestContext(request)
    insertList = []
    menu_dict = {}
    # filter orgs based on logged in user
    if request.method == 'POST':
        new_menu = request.POST.getlist('menu_id')
        print new_menu
        for val in new_menu:
            splitVal = val.split("__")
            instance = MenuRoleMap(role_id=splitVal[0], menu_id=splitVal[1])
            insertList.append(instance)

        MenuRoleMap.objects.all().delete()
        MenuRoleMap.objects.bulk_create(insertList)
        messages.success(request, '<i class="fa fa-check-circle"></i> Access List has been updated successfully!',
                         extra_tags='alert-success crop-both-side')
        return HttpResponseRedirect('/usermodule/role-menu-map-list/')
    else:
        if request.user.is_superuser:
            menu_items = MenuItem.objects.all()
            roles = OrganizationRole.objects.all()
            for role in roles:
                org_menu_list = MenuRoleMap.objects.filter(role=role.id).values_list('menu_id', flat=True)
                menu_dict[role.id] = org_menu_list
        else:
            menu_items = MenuItem.objects.all()
            current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
            if current_user:
                current_user = current_user[0]
            all_organizations = get_recursive_organization_children(current_user.organisation_name, [])
            org_id_list = [org.pk for org in all_organizations]
            roles = OrganizationRole.objects.filter(organization__in=org_id_list)
            for role in roles:
                org_menu_list = MenuRoleMap.objects.filter(role=role.id).values_list('menu_id', flat=True)
                menu_dict[role.id] = org_menu_list

        return render_to_response(
            'usermodule/roles_menu_map_list.html',
            {'menu_items':menu_items, 'menu_dict':menu_dict,'roles':roles},
            context)


# Roles based on Organization CRUD
@login_required
@user_passes_test(admin_check,login_url='/')
def add_role_menu_map(request):
    context = RequestContext(request)
    is_added_role = False
    if request.method == 'POST':
        role_form = RoleMenuMapForm(data=request.POST)
        if role_form.is_valid():
            role_form.save()
            is_added_role = True
            messages.success(request, '<i class="fa fa-check-circle"></i> New access has been added successfully!',
                             extra_tags='alert-success crop-both-side')
            return HttpResponseRedirect('/usermodule/role-menu-map-list/')
        else:
            print role_form.errors
        return HttpResponseRedirect('/usermodule/role-menu-map-list/')
    else:
        if request.user.is_superuser:
            RoleMenuMapForm.base_fields['role'] = forms.ModelChoiceField(queryset=OrganizationRole.objects.all().order_by("organization"),empty_label="Select a Organization Role")
            
        else:
            org_id_list = get_organization_by_user(request.user)
            RoleMenuMapForm.base_fields['role'] = forms.ModelChoiceField(queryset=OrganizationRole.objects.filter(organization__in=org_id_list).order_by("organization"),empty_label="Select a Organization Role")
        role_form = RoleMenuMapForm()
        return render_to_response(
            'usermodule/add_role_menu_map.html',
            {'role_form': role_form,
            'is_added_role': is_added_role},
            context)


@login_required
@user_passes_test(admin_check, login_url='/')
def edit_role_menu_map(request, item_id):
    context = RequestContext(request)
    edited = False
    role_menu_map = get_object_or_404(MenuRoleMap, id=item_id)
    if request.method == 'POST':
        role_form = RoleMenuMapForm(data=request.POST,instance=role_menu_map)
        if role_form.is_valid():
            role_form.save()
            edited = True
            messages.success(request, '<i class="fa fa-check-circle"></i> This access has been edit successfully!',
                             extra_tags='alert-success crop-both-side')
            return HttpResponseRedirect('/usermodule/role-menu-map-list/')
        else:
            print role_form.errors
    else:
        if request.user.is_superuser:
            RoleMenuMapForm.base_fields['role'] = forms.ModelChoiceField(queryset=OrganizationRole.objects.all(),empty_label="Select a Organization Role")
        else:
            org_id_list = get_organization_by_user(request.user)
            RoleMenuMapForm.base_fields['role'] = forms.ModelChoiceField(queryset=OrganizationRole.objects.filter(organization__in=org_id_list),empty_label="Select a Organization Role")
        role_form = RoleMenuMapForm(instance=role_menu_map,initial = {'role': role_menu_map.role,'menu': role_menu_map.menu })
    return render_to_response(
            'usermodule/edit_role_menu_map.html',
            {'id':item_id, 'role_form': role_form,
            'edited': edited},
            context)


@login_required
@user_passes_test(admin_check, login_url='/')
def delete_role_menu_map(request, item_id):
    context = RequestContext(request)
    del_map_item = MenuRoleMap.objects.get(pk = item_id)
    del_map_item.delete()
    messages.success(request, '<i class="fa fa-check-circle"></i> This access has been deleted successfully!',
                     extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect('/usermodule/role-menu-map-list')


# =========================================================
@login_required
@user_passes_test(admin_check, login_url='/')
def organization_roles(request):
    context = RequestContext(request)
    if request.user.is_superuser:
        all_organizations = Organizations.objects.all()
    else:    
        org_id_list = get_organization_by_user(request.user)
        all_organizations = Organizations.objects.filter(pk__in=org_id_list)
    message = None
    if len(all_organizations) == 0:    
        message = "You do not have any Organizations under your supervision."
    return render_to_response(
            'usermodule/organization_roles.html',
            {'all_organizations':all_organizations,"message":message},
            context)


@login_required
@user_passes_test(admin_check, login_url='/')
def user_role_map(request, org_id=None):
    context = RequestContext(request)
    edited = False
    roles = OrganizationRole.objects.filter(organization=org_id)
    users = UserModuleProfile.objects.filter(organisation_name=org_id)
    message = None
    if len(roles) == 0 or len(users) == 0:    
        message = "Your organization must have atleast one user and one role before assignment."
    return render_to_response(
            'usermodule/user_role_map.html',
            {'id':org_id,
            'users' : users,
            'roles' : roles,
            'message':message,
            'edited': edited},
            context)


@login_required
@user_passes_test(admin_check, login_url='/')
def adjust_user_role_map(request, org_id=None):
    context = RequestContext(request)
    is_added = False
    roles = OrganizationRole.objects.filter(organization=org_id)
    users = UserModuleProfile.objects.filter(organisation_name=org_id)
    initial_list = []
    for user_item in users:
        alist = UserRoleMap.objects.filter(user=user_item.pk).values('role')
        mist = []
        for i in alist:
            mist.append( i['role'])
        initial_list.append({'user': user_item.pk,'role':mist,'username': user_item.user.username})

    UserRoleMapfForm.base_fields['role'] = forms.ModelChoiceField(queryset=roles,empty_label=None)
    PermisssionFormSet = formset_factory(UserRoleMapfForm,max_num=len(users))
    new_formset = PermisssionFormSet(initial=initial_list)
    
    if request.method == 'POST':
        new_formset = PermisssionFormSet(data=request.POST)
        for idx,user_role_form in enumerate(new_formset):
            # user_role_form = UserRoleMapfForm(data=request.POST)
            u_id = request.POST['form-'+str(idx)+'-user']
            mist = initial_list[idx]['role']
            current_user = UserModuleProfile.objects.get(pk=u_id)
            results = map(int, request.POST.getlist('role-'+str(idx+1)))
            deleter = list(set(mist) - set(results))
            for role_id in results:
                roley = OrganizationRole.objects.get(pk=role_id)
                try:
                    UserRoleMap.objects.get(user=current_user,role=roley)
                except ObjectDoesNotExist as e:
                    UserRoleMap(user=current_user,role=roley).save()
            for dely in deleter:
                loly = OrganizationRole.objects.get(pk=dely)
                ob = UserRoleMap.objects.get(user=current_user,role=loly).delete()
        messages.success(request, '<i class="fa fa-check-circle"></i> Organization Roles have been adjusted successfully!',
                         extra_tags='alert-success crop-both-side')
        return HttpResponseRedirect('/usermodule/user-role-map/'+org_id)
    
    return render_to_response(
            'usermodule/add_user_role_map.html',
            {
            'id':org_id,
            # 'formset':formset,
            'new_formset':new_formset,
            'roles':roles,
            # 'users':users,
            },
            context)


def error_page(request,message = None):
    context = RequestContext(request)
    if not message:    
        message = "Something went wrong"
    return render_to_response(
            'usermodule/error_404.html',
            {'message':message,
            },
            context)

@csrf_exempt
#@login_required
def sent_datalist(request,username):
    content_user = get_object_or_404(User, username__iexact=str(username))
    print content_user.username
    cursor = connection.cursor()
    json_data_response = []
    #instance_data_json = {}
    try:
        passing_data  = [content_user.id]
        cursor.execute("BEGIN")
        cursor.callproc('get_submitted_data',passing_data)
        tmp_db_value = cursor.fetchall()
        cursor.execute("COMMIT")
	print (tmp_db_value)
        if tmp_db_value is not None:
            for every in tmp_db_value:
                instance_data_json = {}
                #event_type = switch_event_type_label(str(every[1]))
                instance_data_json['hh_id'] = str(every[0])
                instance_data_json['h_man'] = str(every[1])
                instance_data_json['uuid'] = str(every[2])
                instance_data_json['xform_id'] = every[4]
                instance_data_json['date_created'] = str(every[3])
                json_data_response.append(instance_data_json)

           # print json_data_response
        submission_status = 0
    except Exception, e:
        print "db insert error"
        print str(e)
        submission_status = 1
        # Rollback in case there is any error
        connection.rollback()
    finally:
        cursor.close()
        return_value = {
            'submission_status':submission_status,
        }
    return HttpResponse(json.dumps(json_data_response))



######################### Catchment Area ########################
#################################################################
#################################################################


@login_required
def add_children(request):
    id = request.POST.get('id')
    query = "select id,field_name from geo_data where field_parent_id = " + str(id) + ""
    df = pandas.read_sql(query, connection)
    id_ch = df.id.tolist()
    name = df.field_name.tolist()
    all = zip(id_ch, name)
    list_of_dictionary = []
    for id_ch,name in all:
        query = "select id from geo_data where field_parent_id =" + str(id_ch)+ "limit 1"
        df = pandas.read_sql(query, connection)
        if len(df.id.tolist()):
            true = True
        else: true = False
        temp = {"id": id_ch, "text": name, "hasChildren": true, "children": []}
        list_of_dictionary.append(temp)
    return HttpResponse(json.dumps({'id': id,'list_of_dictionary': list_of_dictionary}))

@login_required
def catchment_tree_test(request,user_id):
    query = "select * from geo_data where field_parent_id is null"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    id = df.id.tolist()
    name = df.field_name.tolist()
    all = zip(id,name)
    list_of_dictionary = []
    start  = time.time()
    for id,name in all:
        query = "select id from geo_data where field_parent_id =" + str(id)+ "limit 1"
        df = pandas.read_sql(query, connection)
        if len(df.id.tolist()):
            true = True
        else:
            true = False
        temp = {"id": id, "text": name,"hasChildren":true, "children": []}
        list_of_dictionary.append(temp)
    datasource = json.dumps({'list_of_dictionary': list_of_dictionary})
    check_nodes = get_check_nodes(user_id)
    json_content_dictionary = []
    for each in check_nodes:
        if each:
            query_for_json = "select uploaded_file_path from geo_data where id = " + str(each) + ""
            df = pandas.DataFrame()
            df = pandas.read_sql(query_for_json, connection)
            uploaded_file_path = df.uploaded_file_path.tolist()[0]
            if uploaded_file_path != "cd":
                file = open(uploaded_file_path, 'r')
                json_content = file.read()
                file.close()
            else:
                json_content = "{}"
            json_content_dictionary.append(json_content)
    print("END    "+str(time.time()-start))
    query = "select (SELECT  organization FROM public.usermodule_organizations where id = (select organisation_name_id from usermodule_usermoduleprofile where user_id = " + str(
        user_id) + ")) ,(select employee_id from usermodule_usermoduleprofile where user_id = " + str(
        user_id) + "),(select country from usermodule_usermoduleprofile where user_id = " + str(
        user_id) + "),(select position from usermodule_usermoduleprofile where user_id = " + str(
        user_id) + "),username, email from auth_user where id=" + str(user_id) + ""
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    organization = df.organization.tolist()[0]
    employee_id = df.employee_id.tolist()[0]
    country = df.country.tolist()[0]
    position = df.position.tolist()[0]
    username = df.username.tolist()[0]
    email = df.email.tolist()[0]
    query = "with recursive t as( select id,field_name,field_parent_id from geo_data where id in (select geoid from public.usermodule_catchment_area where user_id = " + str(
        user_id) + ") union all select geo_data.id,geo_data.field_name,geo_data.field_parent_id from geo_data,t where t.field_parent_id = geo_data.id) select distinct id,field_name,field_parent_id from t order by id"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    parent_list = df.id.tolist()
    query = "select node_name from geo_definition"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    geo_def_list = df.node_name.tolist()
    return render(request, "usermodule/catchment_tree_test.html", {'datasource': datasource
        , 'organization': organization
        , 'employee_id': employee_id
        , 'country': country
        , 'position': position
        , 'username': username
        , 'email': email
        , 'user_id': user_id
        , 'check_nodes': check_nodes,'json_content': json_content_dictionary,'parent_list':parent_list,'geo_def_list':json.dumps(geo_def_list)})


def check_for_delete(request):
    id = request.POST.get('id')
    # Dependency Check
    # First if it exists in usermodule_catchment_area
    query_user = "select (select username from auth_user where id = user_id) from public.usermodule_catchment_area where geoid =" + str(id)
    df_user = pandas.DataFrame()
    df_user = pandas.read_sql(query_user, connection)

    # if it exists in organization_catchment_area
    query_org = "select (select organization from usermodule_organizations where id = org_id) from public.organization_catchment_area where geoid =" + str(id)
    df_org = pandas.DataFrame()
    df_org = pandas.read_sql(query_org, connection)

    # if it has any children
    query_child = "select * from public.geo_data where field_parent_id =" + str(id)
    df_child = pandas.DataFrame()
    df_child = pandas.read_sql(query_child, connection)

    extra_info= ""
    # if df_user.empty and df_org.empty and df_child.empty and parent_dependency_check_user(id) and parent_dependency_check_org(id):
    if df_user.empty and df_org.empty and df_child.empty:
        dependency = 0
    elif not df_user.empty:
        extra_info =df_user.username.tolist()[0]
        dependency = 1
    elif not df_org.empty:
        extra_info = df_org.organization.tolist()[0]
        dependency = 2
    else:
        dependency = 3

    return HttpResponse(json.dumps({'dependency':dependency,'extra_info':extra_info}))

def parent_dependency_check_user(geoid):
    query = "with recursive t as( select id,field_name,field_parent_id from geo_data where id =  " + str(geoid) + " union all select geo_data.id,geo_data.field_name,geo_data.field_parent_id from geo_data,t where t.field_parent_id = geo_data.id) select id,field_name,field_parent_id from t order by id"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    parent_list = df.id.tolist()
    print(parent_list)

    query = "select distinct geoid from usermodule_catchment_area"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    geo_list = df.geoid.tolist()

    for each in parent_list:
        if each in geo_list:
            print("User" + str(each))
            return False
    return True


def parent_dependency_check_org(geoid):
    query = "with recursive t as( select id,field_name,field_parent_id from geo_data where id =  " + str(
        geoid) + " union all select geo_data.id,geo_data.field_name,geo_data.field_parent_id from geo_data,t where t.field_parent_id = geo_data.id) select id,field_name,field_parent_id from t order by id"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    parent_list = df.id.tolist()

    query = "select distinct geoid from organization_catchment_area"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    geo_list = df.geoid.tolist()

    for each in parent_list:
        if each in geo_list:
            print("ORG" + str(each))
            return False
    return True


@login_required
def catchment_tree(request, user_id):
    query = "select * from geo_data where field_parent_id is null"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    id = df.id.tolist()
    print "Start"
    print datetime.now()
    list_of_dictionary = []
    for each in id:
        create_dictionary(list_of_dictionary, each)
    datasource = json.dumps({'list_of_dictionary': list_of_dictionary})
    print "END"
    print datetime.now()
    query = "select (SELECT  organization FROM public.usermodule_organizations where id = (select organisation_name_id from usermodule_usermoduleprofile where user_id = " + str(
        user_id) + ")) ,(select employee_id from usermodule_usermoduleprofile where user_id = " + str(
        user_id) + "),(select country from usermodule_usermoduleprofile where user_id = " + str(
        user_id) + "),(select position from usermodule_usermoduleprofile where user_id = " + str(
        user_id) + "),username, email from auth_user where id=" + str(user_id) + ""
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    organization = df.organization.tolist()[0]
    employee_id = df.employee_id.tolist()[0]
    country = df.country.tolist()[0]
    position = df.position.tolist()[0]
    username = df.username.tolist()[0]
    email = df.email.tolist()[0]
    check_nodes = get_check_nodes(user_id)
    
    return render(request, "usermodule/catchment_tree.html", {'datasource': datasource
        , 'organization': organization
        , 'employee_id': employee_id
        , 'country': country
        , 'position': position
        , 'username': username
        , 'email': email
        , 'user_id': user_id
        , 'check_nodes': check_nodes
                                                              })

def create_dictionary(list_of_dictionary, each):
    query = "select field_name from geo_data where id = " + str(each) + ""
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    name = df.field_name.tolist()[0]
    dict = {'id': each, 'text': name, 'children': []}
    query = "select id from geo_data where field_parent_id = " + str(each) + ""
    df = pandas.read_sql(query, connection)
    id = df.id.tolist()
    for each in id:
        create_dictionary(dict['children'], each)
    list_of_dictionary.append(dict)
    


def database(query):
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    cursor.close()


@login_required
def catchment_data_insert(request):
    result_set = request.POST.get('result_set').split(',')
    user_id = int(request.POST.get('user_id'))
    delete_prev_catchment_record(user_id)
    result_set = list(set(result_set))
    for each in result_set:
        if each:
            query = "INSERT INTO public.usermodule_catchment_area (user_id, geoid) VALUES(" + str(user_id) + ", " + str(
                each) + ")"
            database(query)
    return HttpResponseRedirect('/usermodule/')


def get_check_nodes(user_id):
    query = "select * from usermodule_catchment_area where user_id = " + str(user_id) + ""
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    check_nodes = df.geoid.tolist()
    return check_nodes


def delete_prev_catchment_record(user_id):
    query = "delete from usermodule_catchment_area where user_id = " + str(user_id) + ""
    database(query)


@login_required
def form_def(request):
    if request.POST:
        df = pandas.DataFrame()
        node_par = "select id from geo_definition where node_name = '" + str(request.POST.get('node_parent')) + "' "
        df = pandas.read_sql(node_par, connection)
        node = df.values.tolist()
        if len(node):
            query = "INSERT INTO geo_definition(node_name, node_parent)VALUES ('" + str(request.POST.get(
                'node_name')) + "' , " + str(node[0][0]) + ")"
        else:
            query = "INSERT INTO geo_definition(node_name)VALUES ('" + str(request.POST.get(
                'node_name')) + "' )"
        database(query)
        return HttpResponseRedirect("/usermodule/geo_def_data/")
    check = pandas.DataFrame()
    option = "select * from geo_definition"
    check = pandas.read_sql(option, connection)
    node_val = check.node_name
    return render(request, "usermodule/form_definition.html", {"node_val": node_val})


@login_required
def form(request):
    if request.POST:
        if request.FILES:
            myfile = request.FILES['geojsonfile']
            url = "onadata/media/uploaded_files/"
            userName = request.user  # "Jubair"
            fs = FileSystemStorage(location=url)
            myfile.name = str(datetime.now()) + "_" + str(userName) + "_" + str(myfile.name)
            filename = fs.save(myfile.name, myfile)
            full_file_path = "onadata/media/uploaded_files/" + myfile.name
            file = open(full_file_path, 'r')
            json_content = file.read()
            file.close()
        else:
            json_content = '{}'
            full_file_path = 'cd'
        parent = int(request.POST.get("parent_id"))
        print(request.POST.get('geocode'))
        if parent != -1:
            query = "INSERT INTO geo_data(field_name, field_parent_id,field_type_id,geocode,geojson,uploaded_file_path) VALUES('" + str(
                request.POST.get('field_name')) + "'," + str(
                request.POST.get('field_parent_' + str(parent) + '')) + "," + str(
                request.POST.get('field_type')) + ",'" + str(request.POST.get('geocode')) + "','" + str(
                json_content) + "','" + str(full_file_path) + "')"
        else:
            query = "INSERT INTO geo_data(field_name, field_type_id,geocode,geojson,uploaded_file_path) VALUES('" + str(
                request.POST.get('field_name')) + "'," + str(request.POST.get('field_type')) + ",'" + str(
                request.POST.get('geocode')) + "','" + str(json_content) + "','" + str(full_file_path) + "')"
        database(query)
        return HttpResponseRedirect("/usermodule/geo_list/")
    check = pandas.DataFrame()
    option = "select * from geo_definition"
    check = pandas.read_sql(option, connection)
    node_val = check.node_name.tolist()
    node_id = check.id.tolist()
    node = json.dumps({"node_val": node_val, "node_id": node_id})
    list = zip(node_id, node_val)
    division_geocode_query = "select geocode from geo_data where field_parent_id  is null"
    df = pandas.DataFrame()
    df = pandas.read_sql(division_geocode_query, connection)
    division_geocode = df.geocode.tolist()

    division_type_id_query = "select id from geo_definition where node_parent  is null"
    df = pandas.DataFrame()
    df = pandas.read_sql(division_type_id_query, connection)
    division_id = df.id.tolist()[0]
    return render(request, 'usermodule/form.html', {'node': list, 'division_geocode': json.dumps(division_geocode),'division_id':division_id})


@login_required
def form_drop(request):
    if request.POST:
        df = pandas.DataFrame()
        fb = str(request.POST.get('field_type'))
        field_name_query = "select * from geo_data where field_type_id = " + str(request.POST.get('field_type')) + ""
        df = pandas.read_sql(field_name_query, connection)
        field_name = df.field_name.tolist()
        field_id = df.id.tolist()
        field_type_name_query = "select * from geo_definition where id = " + str(request.POST.get('field_type')) + ""
        df = pandas.read_sql(field_type_name_query, connection)
        field_type_name = df.node_name.tolist()
    field_name = json.dumps({'field_name': field_name, 'field_id': field_id, 'field_type_name': field_type_name})
    return HttpResponse(field_name)


@login_required
def filtering(request):
    if request.POST:
        df = pandas.DataFrame()
        field_name_query = "select * from geo_data where field_type_id = " + str(
            request.POST.get('field_type_id')) + " and field_parent_id = " + str(
            request.POST.get('field_parent_id')) + ""
        df = pandas.read_sql(field_name_query, connection)
        geocode = df.geocode.tolist()
        field_name = df.field_name.tolist()
        field_id = df.id.tolist()
        field_type_query = "select * from geo_definition where id=" + str(request.POST.get('field_type_id')) + ""
        df = pandas.read_sql(field_type_query, connection)
        field_type = df.node_name.tolist()

        field_parent_geocode = "select geocode from geo_data where id = "+str(request.POST.get('field_parent_id'))
        df = pandas.DataFrame()
        df = pandas.read_sql(field_parent_geocode,connection)
        if not df.empty:
            parent_geocode = df.geocode.tolist()[0]
        else:
            parent_geocode = -1
    field_name = json.dumps({'field_name': field_name, 'field_id': field_id, 'field_type': field_type,'geocode':geocode,'parent_geocode':parent_geocode})
    return HttpResponse(field_name)


@login_required
def tree(request):
    id = int(request.POST.get('objet'))
    # print(id)
    list = []
    tree_construct(id, list)
    response_record = {}
    if len(list):
        for i in range(len(list) - 1):
            response_record[list[i]] = list[i + 1]
        response_record[list[len(list) - 1]] = id
        parent = list[len(list) - 1]
    else:
        parent = -1
    print(parent)
    print(response_record)
    return HttpResponse(json.dumps({'response_record': response_record,'parent_id':parent }))


def tree_construct(id, list):
    query = "select * from geo_definition where id = " + str(id) + ""
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    node_parent = df.node_parent.tolist()
    if df.empty or node_parent[0] is None:
        return
    else:
        tree_construct(node_parent[0], list)
    list.append(node_parent[0])
    return


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


def __db_fetch_values(query):
    """
        Fetch database result set as list of tuples

        Args:
            query (str): raw query string

        Returns:
            str: Returns database result set as list of tuples
    """
    cursor = connection.cursor()
    cursor.execute(query)
    fetch_val = cursor.fetchall()
    cursor.close()
    data_list = []
    for each_val in fetch_val:
        data_list.append(list(each_val))
    return data_list


@login_required
def geo_def_list(request):
    geo_def_query = "with t as (select * from geo_definition) select t.id ,t.node_name , (select node_name from geo_definition where id = t.node_parent) as node_parent_name from t"
    geo_def_data = json.dumps(__db_fetch_values_dict(geo_def_query))
    return render(request, 'usermodule/geo_def_list.html', {
        'geo_def_data': geo_def_data
    })


@login_required
def geo_list(request):
    query = "select id,field_name,(select node_name from geo_definition where id = field_type_id) as field_type,geocode from geo_data"
    # geo_def_data = json.dumps(__db_fetch_values_dict(query))
    geo_def_data = __db_fetch_values(query)
    return render(request,'usermodule/geo_list.html',{
      'geo_def_data':geo_def_data
    })


@login_required
def edit_form_definition(request, form_definition_id):
    check = pandas.DataFrame()
    option = "select * from geo_definition"
    check = pandas.read_sql(option, connection)
    node_val = check.node_name
    query_specific = "with t as (select * from geo_definition) select t.id ,t.node_name , (select node_name from geo_definition where id = t.node_parent) as node_parent_name from t where t.id =" + str(
        form_definition_id) + ""
    check = pandas.read_sql(query_specific, connection)
    node_name = check.node_name.tolist()[0];
    node_parent_name = check.node_parent_name.tolist()[0];
    return render(request, "usermodule/edit_form_definition.html", {"node_val": node_val,
                                                                    'node_parent_name': node_parent_name,
                                                                    'node_name': node_name,
                                                                    "form_definition_id": form_definition_id})


@login_required
def update_form_definition(request):
    if request.POST:
        df = pandas.DataFrame()
        node_par = "select id from geo_definition where node_name = '" + str(request.POST.get('node_parent')) + "' "
        df = pandas.read_sql(node_par, connection)
        node = df.values.tolist()
        delete_query = "delete  from geo_definition where id=" + str(int(request.POST.get('form_definition_id'))) + ""
        database(delete_query)
        if len(node):
            query = "INSERT INTO geo_definition(id,node_name, node_parent)VALUES (" + str(
                int(request.POST.get('form_definition_id'))) + ",'" + str(request.POST.get('node_name')) + "' , " + str(
                node[0][0]) + ")"
        else:
            query = "INSERT INTO geo_definition(id,node_name)VALUES (" + str(
                int(request.POST.get('form_definition_id'))) + ",'" + str(request.POST.get('node_name')) + "' )"
        database(query)
    return HttpResponseRedirect("/usermodule/geo_def_data/")


@login_required
def delete_form_definition(request, form_definition_id):
    list_of_form_definition = []
    form_definition_calculation(list_of_form_definition, form_definition_id)
    return HttpResponseRedirect("/usermodule/geo_def_data/")


def form_definition_calculation(list_of_form_definition, form_definition_id):
    list_of_form_definition.append(int(form_definition_id))
    query = "select * from geo_definition where node_parent=" + str(form_definition_id) + ""
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    id = df.id.tolist()
    query = "select * from geo_data where field_type_id=" + str(form_definition_id) + ""
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    form_id = df.id.tolist()
    for each in form_id:
        delete_from_catchment_area = "delete from usermodule_catchment_area where geoid = " + str(each) + ""
        database(delete_from_catchment_area)
    delete_query = "delete from geo_definition where id =" + str(int(form_definition_id)) + ""
    database(delete_query)
    delete_query = "delete from geo_data where field_type_id =" + str(int(form_definition_id)) + ""
    database(delete_query)
    for each in id:
        form_definition_calculation(list_of_form_definition, each)


@login_required
def edit_form(request,form_id):
    check = pandas.DataFrame()
    option = "select * from geo_definition"
    check = pandas.read_sql(option, connection)
    node_val = check.node_name.tolist()
    node_id = check.id.tolist()
    node = json.dumps({"node_val": node_val, "node_id": node_id})
    list = zip(node_id, node_val)
    query_specific = "select field_name,field_parent_id,field_type_id,(select node_name from geo_definition where id = field_type_id ) as field_type,geocode,uploaded_file_path from geo_data where id =" + str(
        form_id) + ""
    check = pandas.read_sql(query_specific, connection)
    field_parent_id = check.field_parent_id.tolist()[0]
    field_name = check.field_name.tolist()[0]
    field_type = check.field_type.tolist()[0]
    geocode = check.geocode.tolist()[0]
    print(geocode)
    field_type_id = check.field_type_id.tolist()[0]
    uploaded_file_path = check.uploaded_file_path.tolist()[0]
    list_of_id_of_parents = []
    list_of_name_of_parents = []
    if field_parent_id is not None:
        calculate_parents(list_of_id_of_parents, list_of_name_of_parents, field_parent_id)
    list_of_both = json.dumps(
        {'list_of_id_of_parents': list_of_id_of_parents, 'list_of_name_of_parents': list_of_name_of_parents})

    if field_parent_id is not None:
        field_name_query = "select geocode from geo_data where field_type_id = " + str(
            field_type_id) + " and field_parent_id = " + str(field_parent_id) + ""
    else:
        field_name_query = "select geocode from geo_data where field_type_id = " + str(
            field_type_id) + " and field_parent_id  is null"
    df = pandas.read_sql(field_name_query, connection)
    all_geocode = df.geocode.tolist()

    # Dependency Check
    # First if it exists in usermodule_catchment_area
    query_user = "select * from public.usermodule_catchment_area where geoid =" + str(form_id)
    df_user = pandas.DataFrame()
    df_user = pandas.read_sql(query_user, connection)

    # if it exists in organization_catchment_area
    query_org = "select * from public.organization_catchment_area where geoid =" + str(form_id)
    df_org = pandas.DataFrame()
    df_org = pandas.read_sql(query_org, connection)

    # if it has any children
    query_child = "select * from public.geo_data where field_parent_id =" + str(form_id)
    df_child = pandas.DataFrame()
    df_child = pandas.read_sql(query_child, connection)

    if df_user.empty and df_org.empty and df_child.empty and parent_dependency_check_user(form_id) and parent_dependency_check_org(form_id):
        dependency = 0
    else:
        dependency = 1

    return render(request, 'usermodule/edit_form.html', {'node': list,
                                                         'form_id': form_id,
                                                         'field_parent_id': field_parent_id,
                                                         'field_name': field_name,
                                                         'field_type': field_type,
                                                         'geocode': geocode,
                                                         'uploaded_file_path': uploaded_file_path,
                                                         'field_type_id': field_type_id,
                                                         'list_of_both': list_of_both,
                                                         'dependency': dependency,
                                                         'all_geocode': json.dumps(all_geocode)
                                                         })



def calculate_parents(list_of_id_of_parents,list_of_name_of_parents, field_parent_id):
    query="select * from geo_data where id="+str(field_parent_id)+""
    df = pandas.DataFrame()
    df = pandas.read_sql(query,connection)
    id = df.id.tolist()[0]
    field_name = df.field_name.tolist()[0]
    field_parent_id = df.field_parent_id.tolist()[0]
    list_of_id_of_parents.append(id)
    list_of_name_of_parents.append(field_name)
    if field_parent_id is not None:
        calculate_parents(list_of_id_of_parents,list_of_name_of_parents,field_parent_id)


@login_required
def update_form(request):
    if request.POST:
        if request.FILES:
            myfile = request.FILES['geojsonfile']
            url = "onadata/media/uploaded_files/"
            userName = request.user  # "Jubair"
            fs = FileSystemStorage(location=url)
            myfile.name = str(datetime.datetime.now()) + "_" + str(userName) + "_" + str(myfile.name)
            filename = fs.save(myfile.name, myfile)
            full_file_path = "onadata/media/uploaded_files/" + myfile.name
            file = open(full_file_path, 'r')
            json_content = file.read()
            file.close()
        else:
            query = "select geojson,uploaded_file_path from geo_data where id = " + str(request.POST.get("form_id"))
            df = pandas.DataFrame()
            df = pandas.read_sql(query, connection)
            if df.empty:
                json_content = '{}'
                full_file_path = 'cd'
            else:
                json_content = json.dumps(df.geojson.tolist()[0])
                full_file_path = df.uploaded_file_path.tolist()[0]
        print("*****************Update FORM **********")
        parent = int(request.POST.get("parent_id"))
        if parent != -1:
            query = "UPDATE public.geo_data SET field_name='"+ str(request.POST.get('field_name'))+"', field_parent_id="+str(request.POST.get('field_parent_' + str(parent) + '')) +", field_type_id="+ str(request.POST.get('field_type'))+", geocode='"+ str(request.POST.get('geocode'))+"', geojson='"+ str(json_content)+"', uploaded_file_path='"+str(full_file_path)+"' WHERE id="+str(request.POST.get("form_id"))
        else:
            query = "UPDATE public.geo_data SET field_name='"+ str(request.POST.get('field_name'))+"', field_type_id="+ str(request.POST.get('field_type'))+", geocode='"+ str(request.POST.get('geocode'))+"', geojson='"+ str(json_content)+"', uploaded_file_path='"+str(full_file_path)+"' WHERE id="+str(request.POST.get("form_id"))+""
        database(query)
    return HttpResponseRedirect("/usermodule/geo_list/")


@login_required
def delete_form(request,form_id):
    # Dependency Check
    # First if it exists in usermodule_catchment_area
    query_user = "select * from public.usermodule_catchment_area where geoid =" + str(form_id)
    df_user = pandas.DataFrame()
    df_user = pandas.read_sql(query_user, connection)

    # if it exists in organization_catchment_area
    query_org = "select * from public.organization_catchment_area where geoid =" + str(form_id)
    df_org = pandas.DataFrame()
    df_org = pandas.read_sql(query_org, connection)

    # if it has any children
    query_child = "select * from public.geo_data where field_parent_id =" + str(form_id)
    df_child = pandas.DataFrame()
    df_child = pandas.read_sql(query_child, connection)

    if df_user.empty and df_org.empty and df_child.empty:
        delete_child(int(form_id))
    return HttpResponseRedirect("/usermodule/geo_list/")


def delete_child(form_id):
    query = "select * from geo_data where field_parent_id = "+str(form_id)+""
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    id = df.id.tolist()
    query = "select * from geo_data where id = " + str(form_id) + ""
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    id = df.id.tolist()
    uploaded_file_path = df.uploaded_file_path.tolist()
    if len(uploaded_file_path) and uploaded_file_path[0] != "cd":
        os.remove(uploaded_file_path[0])
    delete_query = "delete from geo_data where id = "+str(form_id)+""
    database(delete_query)
    delete_from_catchment_area = "delete from usermodule_catchment_area where geoid = "+str(form_id)+""
    database(delete_from_catchment_area)
    for each in id:
        delete_child(each)


@login_required
def json_data_fetch(request):
    list_of_selected_node = request.POST.get('id')
    list_of_selected_node = list_of_selected_node[1:len(list_of_selected_node) - 1].split(',')
    json_content_dictionary = []
    for each in list_of_selected_node:
        if each:
            query_for_json = "select uploaded_file_path from geo_data where id = " + str(each) + ""
            df = pandas.DataFrame()
            df = pandas.read_sql(query_for_json, connection)
            uploaded_file_path = df.uploaded_file_path.tolist()[0]
            if uploaded_file_path != "cd":
                file = open(uploaded_file_path, 'r')
                json_content = file.read()
                file.close()
            else:
                json_content = "{}"
            json_content_dictionary.append(json_content)
        # json_content = json.loads(json_content)
    # print(json_content_dictionary)
    return  HttpResponse(json.dumps({'json_content': json_content_dictionary}))




#mobile save user
@csrf_exempt
def save_user(request):
    """data = {
                "UserName" : "tup_2",
                "FirstName" : "Md.",
                "LastName" : "Asaduzzaman",
                "Email" : "asad@mpower-social.com",
                "Password" : "12345678",
                "Organization" : "BRAC",
                "Country" : "BGD",
                "IsAdmin" : 0
                }


    """

    print request.body
    json_string = request.body
    # json_string = data
    print json_string
    data = json.loads(json_string)
    submitted_data = {}
    submitted_data['username'] = data['UserName']
    submitted_data['password_repeat'] = data['Password']
    
    submitted_data['first_name'] = data['FirstName'][0].upper() + data['FirstName'][1:]
    submitted_data['last_name'] = data['LastName'][0].upper() + data['LastName'][1:]
    submitted_data['country'] = data['Country']
    
    
    
    if data['IsAdmin']:
        submitted_data['admin'] = True
    else:
        submitted_data['admin'] = False
    submitted_data['password'] = data['Password']
    if 'Email' in data:
    	  submitted_data['email'] = data['Email']
    if 'position' in data:
    	  submitted_data['position'] = data['position']
    if 'employee_id'in data:
    	  submitted_data['employee_id'] = data['employee_id']
		
    if 'Organization'in data:
    	  submitted_data['organisation_name'] = data['Organization']

    # user_form = UserForm(username=data['UserName'], email=data['Email'], password=data['Password'], password_repeat=data['Password'])
    user_form = UserForm(data=submitted_data)
    profile_form = UserProfileForm(data=submitted_data, admin_check=True)

    if user_form.is_valid() and profile_form.is_valid():

        user = user_form.save()
        form_bool_value = False

        encrypted_password = make_password(user.password)
        user.password = encrypted_password
        user.save()

        profile = profile_form.save(commit=False)

        profile.user = user
        expiry_months_delta = 3

        next_expiry_date = (datetime.today() + timedelta(expiry_months_delta * 365 / 12))
        profile.expired = next_expiry_date
        profile.admin = form_bool_value

        profile.save()

        main_user_profile = UserProfile(user=user)
        main_user_profile.save()

        registered = True

        passwordHistory = UserPasswordHistory(user_id=user.id, date=datetime.now())
        passwordHistory.password = encrypted_password
        passwordHistory.save()

        return HttpResponse('success', status=200)

    else:
        print user_form
        print "###################"
        print user_form.errors
        print profile_form.errors
        return HttpResponse('User creation failed', status=409)

    print data
    return HttpResponse('no action')

def upload_csv(request):
    data = {}


    # if not GET, then proceed
    if "POST" == request.method:
        csv_file = request.FILES["csv_file"]
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'File is not CSV type')
            return HttpResponseRedirect("/usermodule/upload/csv")
        # if file is too large, return
        if csv_file.multiple_chunks():
            messages.error(request, "Uploaded file is too big (%.2f MB)." % (csv_file.size / (1000 * 1000),))
            return HttpResponseRedirect(reverse("usermodule:upload_csv"))

        file_data = csv_file.read().decode("utf-8")

        lines = file_data.split("\n")
        # loop over the lines and save them in db. If error , store as string and then display

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="user_reject_list.csv"'
        writer = csv.writer(response)
        writer.writerow(str(lines[0]).split(",")+['Error'])
        print len(lines)
        for line in lines[1:]:

            fields = str(line).split(",")
            if len(fields)<10:
                return response
            submitted_data = {}
            submitted_data['username'] = str(fields[0])
            print fields[1]
            submitted_data['first_name'] = str(fields[1])
            submitted_data['last_name'] = str(fields[2])
            submitted_data['email'] = str(fields[3])
            submitted_data['password'] = str(fields[4])
            submitted_data['password_repeat'] = str(fields[5])
            submitted_data['country'] = str(fields[9])
            organization = str(fields[8])
            org = Organizations.objects.filter(organization = organization).first()
	    
            if org is not None:
                submitted_data['organisation_name'] = org.id
            submitted_data['admin'] = str(fields[6])
            submitted_data['employee_id'] = str(fields[7])
            submitted_data['position'] = str(fields[10])

            try:
                print "user creation started"
                user_form = UserForm(submitted_data)
                profile_form = UserProfileForm(submitted_data)
                if user_form.is_valid() and profile_form.is_valid():
                    user = user_form.save()
                    if submitted_data['admin'].lower() == 'false':
                        form_bool_value = False
                    else:
                        form_bool_value = True

                    # encrypted password is saved so that it can be saved in password history table
                    encrypted_password = make_password(user.password)
                    user.password = encrypted_password
                    user.save()
                    profile = profile_form.save(commit=False)
                    # profile.organisation_name = request.POST.get("organisation_name", "-1")
                    profile.user = user
                    expiry_months_delta = 3
                    # Date representing the next expiry date
                    next_expiry_date = (datetime.today() + timedelta(expiry_months_delta * 365 / 12))
                    profile.expired = next_expiry_date
                    profile.admin = form_bool_value

                    profile.save()

                    # kobo main/models/UserProfile
                    main_user_profile = UserProfile(user=user)
                    main_user_profile.save()

                    # Update our variable to tell the template registration was successful.
                    registered = True

                    # insert password into password history
                    passwordHistory = UserPasswordHistory(user_id=user.id, date=datetime.now())
                    passwordHistory.password = encrypted_password
                    passwordHistory.save()

                    print "user created"
                    print user_form
                else:
                    error_string = ','.join(user_form.error_class.as_text(v) for k, v in user_form.errors.items())

                    error_string += ','.join(profile_form.error_class.as_text(v) for k, v in profile_form.errors.items())
		    print error_string
                    writer.writerow(fields+[error_string])
            except Exception as e:
                logging.getLogger("error_logger").error(user_form.errors.as_json())
                print "checking"
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        logging.getLogger("error_logger").error(user_form.errors.as_json())
        return response
                # pass



    return render(request, "usermodule/user_creation.html", data)




############################# FORM PERMISSION (ZINIA) #####################

"""Form settings Code"""

def single_query(query):
    """function for  query where result is single"""

    fetchVal = data_connection(query)
    strType = map(str, fetchVal[0])
    ans = strType[0]
    return ans

def data_connection(queryr):
    try:
        cursor = connection.cursor()
        cursor.execute(queryr)
        fetchVal = cursor.fetchall()
        # Commit the changes to the database_
        connection.commit()
        # Close communication with the PostgreSQL database
        cursor.close()
        return fetchVal
    except (Exception) as error:
        print(error)
    finally:
        if connection is not None:
            connection.close()


def get_role(org_id_list):
    org_id_list = str(map(str, org_id_list))
    org_id_list = org_id_list.replace('[', '(').replace(']', ')')
    query = "SELECT r.id, organization_id, role, organization FROM public.usermodule_organizationrole r, public.usermodule_organizations o where r.organization_id=o.id and o.id in "+str(org_id_list);
    fetchVal = data_connection(query)
    role_data = []
    for eachval in fetchVal:
        temp = list(eachval)
        role_data.append(temp)
    return role_data


def get_role_permission(id_string):
    query = "select id, xform_id, role_id, can_view, can_submit, can_edit, can_delete, can_setting from public.rolewiseform where xform_id = %d" % (
    id_string)
    permission_data = []
    fetchVal = data_connection(query)
    for eachval in fetchVal:
        temp = list(eachval)
        permission_data.append(temp)
    return permission_data


def checking_change_permission(view_list, edit_list, submit_list, delete_list, role_list, permission_list):
    """ """
    changed_role = {}
    print view_list
    #checking if permission of role has changed from its previous condition if changed then true else it will be false
    for p in permission_list:
        if str(p[2]) in view_list and p[3] == 0:
            print "view1"
            changed_role[p[2]] = True
        elif str(p[2]) in submit_list and p[4] == 0:
            print "submit1"
            changed_role[p[2]] = True
        elif str(p[2]) in edit_list and p[5] == 0:
            print "edit1"
            changed_role[p[2]] = True
        elif str(p[2]) in delete_list and p[6] == 0:
            print "delete1"
            changed_role[p[2]] = True
        elif str(p[2]) not in view_list and p[3] == 1:
            print str(p[2]) + " view2"
            changed_role[p[2]] = True
        elif str(p[2]) not in submit_list and p[4] == 1:
            print "submit2"
            changed_role[p[2]] = True
        elif str(p[2]) not in edit_list and p[5] == 1:
            print "edit2"
            changed_role[p[2]] = True
        elif str(p[2]) not in delete_list and p[6] == 1:
            print "delete2"
            changed_role[p[2]] = True
        else:
            changed_role[p[2]] = False
    return changed_role


def edit_table(query):
    try:
        print query
        # create a new cursor
        cur = connection.cursor()
        # execute the UPDATE  statement
        cur.execute(query)
        # get the number of updated rows
        vendor_id = cur.fetchone()[0]
        print vendor_id
        # Commit the changes to the database_
        connection.commit()
        # Close communication with the PostgreSQL database
        cur.close()
    except (Exception) as error:
        print(error)
    finally:
        if connection is not None:
            connection.close()


@csrf_exempt
def startpage(request, username, id_string):
    query = "select id from logger_xform where id_string = '%s'" % (id_string)
    form_id = int(single_query(query))

    ####
    current_user = UserModuleProfile.objects.filter(user_id=request.user.id)
    if current_user:
        current_user = current_user[0]

    # fetching all organization recursively of current_user
    all_organizations = get_recursive_organization_children(current_user.organisation_name, [])
    org_id_list = [org.pk for org in all_organizations]

    if request.method == 'POST':
        # id_string = request.POST.get('id_string');
        # query = "select id from logger_xform where id_string = '%s'" % (id_string)
        # form_id = int(single_query(query))
        view_list = request.POST.getlist('view_id[]');
        edit_list = request.POST.getlist('edit_id[]');
        submit_list = request.POST.getlist('submit_id[]');
        delete_list = request.POST.getlist('delete_id[]');
        role_list = get_role(org_id_list)
        permission_role = get_role_permission(form_id)
        changed_role = checking_change_permission(view_list, edit_list, submit_list, delete_list, role_list,
                                                  permission_role)
        for r in role_list:
            view_flag = edit_flag = delete_flag = submit_flag = 0
            if r[0] in changed_role and changed_role[r[0]] == True:
                if str(r[0]) in view_list:
                    view_flag = 1
                if str(r[0]) in edit_list:
                    edit_flag = 1
                if str(r[0]) in submit_list:
                    submit_flag = 1
                if str(r[0]) in delete_list:
                    delete_flag = 1
                query = "UPDATE public.rolewiseform SET can_view = %d, can_submit =  %d, can_edit= %d , can_delete=%d where xform_id = %d and role_id=%d" % (
                    view_flag, submit_flag, edit_flag, delete_flag, form_id, r[0])
                edit_table(query)
            else:
                if str(r[0]) in view_list + edit_list + submit_list + delete_list and r[0] not in changed_role:
                    if str(r[0]) in view_list:
                        view_flag = 1
                    if str(r[0]) in edit_list:
                        edit_flag = 1
                    if str(r[0]) in submit_list:
                        submit_flag = 1
                    if str(r[0]) in delete_list:
                        delete_flag = 1
                    query = "INSERT INTO public.rolewiseform ( xform_id, role_id, can_view, can_submit, can_edit, can_delete, can_setting) VALUES (%d, %d, %d, %d, %d, %d, 0) RETURNING id;" % (
                        form_id, r[0], view_flag, submit_flag, edit_flag, delete_flag)
                    edit_table(query)
	messages.success(request,'<i class="fa fa-check-circle"></i> Roles has been updated successfully!',extra_tags='alert-success crop-both-side')



    context = {
            'role_list': get_role(org_id_list),
            'permission_data': get_role_permission(form_id),
            'id_string': id_string
        }
    return render(request, 'usermodule/startpage.html', context)


########################################################







