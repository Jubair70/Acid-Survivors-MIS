from django.db import models
from onadata.apps.scheduling.schedule_utils import create_user_schedule, update_schedule_status
from onadata.apps.unicef.models import GeoPSU
# for raw sql
from django.db import connection
from collections import namedtuple
# user profile information
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from onadata.apps.usermodule.models import UserModuleProfile


class Beneficiary(models.Model):
    user_id = models.CharField(max_length=200)
    instance_id = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    household_id = models.IntegerField(default=0)
    head_member = models.BooleanField(default=False)
    beneficiary_id = models.CharField(max_length=200)
    beneficiary_name = models.CharField(max_length=200)
    unicef_id = models.CharField(max_length=100)
    gender = models.CharField(max_length=200, null=True, default='', blank=True)
    age_year = models.CharField(max_length=200, null=True, default='', blank=True)
    age_month = models.CharField(max_length=200, null=True, default='', blank=True)
    last_date_of_pregnancy = models.CharField(max_length=200, null=True, default='', blank=True)
    pregnant_lactating = models.CharField(max_length=200, null=True, default='', blank=True)
    highest_grade_passed = models.CharField(max_length=200, null=True, default='', blank=True)

    class Meta:
        app_label = 'scheduling'


def insert_beneficiary_info(username, instance):
    group_member_list = instance.json.get('group_member')
    if group_member_list is None:
        return

    is_head_man = True;
    if already_headman_exists(instance.json.get('HH_Id')):
        is_head_man = False;

    """
    find data sender geo hierarchy to generate unicef_id
    """
    counting = existing_beneficiary_number_in_household(instance.json.get('HH_Id'))

    if counting is None or counting <= 0:
        """
        Create Safe Water Supply and Sanitation (one time) for each household after getting Household Registration form
        """
        create_user_schedule(username, instance, '', 'safe_water_supply')
        create_user_schedule(username, instance, '', 'sanitation')

    user = get_object_or_404(User, username=username.lower())
    user_module_profile = UserModuleProfile.objects.get(user=user)
    psu = user_module_profile.psu

    _ret_val = ''
    for group_member in group_member_list:
        counting += 1
        unicef_id = create_unicef_id(username, instance.json.get('HH_Id'), counting)
        beneficiary_id = instance.json.get('HH_Id') + '0' + str(counting)

        beneficiary = Beneficiary()
        beneficiary.user_id = username
        beneficiary.instance_id = instance.id
        beneficiary.household_id = instance.json.get('HH_Id')
        beneficiary.head_member = is_head_man
        beneficiary.beneficiary_id = beneficiary_id
        beneficiary.beneficiary_name = group_member.get('group_member/Member_name')
        beneficiary.unicef_id = unicef_id
        beneficiary.gender = group_member.get('group_member/Gender')
        beneficiary.age_year = group_member.get('group_member/Age_year')
        beneficiary.age_month = group_member.get('group_member/Age_month')
        beneficiary.last_date_of_pregnancy = group_member.get('group_member/Last_delivery_month')
        beneficiary.pregnant_lactating = group_member.get('group_member/Pregnant_lactating')
        beneficiary.highest_grade_passed = group_member.get('group_member/Highest_grade_passed')
        beneficiary.save()
        is_head_man = False

        """
        Create return message for mobile user with beneficiary name and id.
        """
        _ret_val += '\n' + '<' + beneficiary.beneficiary_name + '> <' + beneficiary.beneficiary_id + '>'
        print('\n\n\n\n\n\n creating return message = ')
        print(_ret_val)
        print('\n\n\n\n\n')
        """
        create schedule for each beneficiary.
        """
        create_next_schedule_form(username, instance, beneficiary)
    return _ret_val


def existing_beneficiary_number_in_household(h_id):
    beneficiary_list = Beneficiary.objects.filter(household_id=h_id).distinct()
    if beneficiary_list is not None:
        return len(beneficiary_list)
    else:
        return 0


def already_headman_exists(h_id):
    headman = Beneficiary.objects.filter(household_id=h_id, head_member=True).first()
    if headman is not None and headman.household_id is not None:
        return True
    else:
        return False


def create_unicef_id(user_name, hh_id, count):
    user = get_object_or_404(User, username=user_name.lower())
    user_module_profile = UserModuleProfile.objects.get(user=user)
    psu = user_module_profile.psu;
    print('\n\n\n\n\n\n creating unicef_id where psu = \n')
    print(psu)
    print('\n\n\n\n\n\n creating unicef_id where division_id = \n')
    print(psu.geo_division.geo_id)
    unicef_id = str(
        psu.geo_division.geo_id + psu.geo_district.geo_id + psu.geo_upazilla.geo_id + psu.geo_union.geo_id + psu.psu_id) + str(
        hh_id) + '0' + str(count)
    return unicef_id


def create_next_schedule_form(username, instance, beneficiary):
    """
    :type beneficiary: object
    """
    """
    3) Maternal Diet schedule form will be generated when pregnant_lactating question value equal to 1
    """
    if beneficiary.pregnant_lactating is not None and beneficiary.pregnant_lactating == '1':
        create_user_schedule(username, instance, beneficiary.beneficiary_id, "maternal_diet")

    """
    4) IFA schedule form will be generated when Last_delivery_month question value equal to 1
    """
    if beneficiary.last_date_of_pregnancy is not None and beneficiary.last_date_of_pregnancy == '1':
        create_user_schedule(username, instance, beneficiary.beneficiary_id, "ifa")

    """
    5) ANC schedule form will be generated when Last_delivery_month question value equal to 2
    """
    if beneficiary.last_date_of_pregnancy is not None and beneficiary.last_date_of_pregnancy == '2':
        create_user_schedule(username, instance, beneficiary.beneficiary_id, "anc")

    """
    6) Birth Registration schedule form will be when generated Age_year question value would be less than 1
    """
    if beneficiary.age_year is not None and 0 <= int(beneficiary.age_year) <= 1:
        create_user_schedule(username, instance, beneficiary.beneficiary_id, "birth_registration")
    """
    7) Early BF schedule form will be when generated Age_year question value equal to 00
    """
    if beneficiary.age_year is not None and beneficiary.age_year == '00':
        create_user_schedule(username, instance, beneficiary.beneficiary_id, "early_bf")

    """
    8) Exclusive BF schedule form will be when generated Age_month question value greater than equal to 0 and less than equal to 5
    """
    if beneficiary.age_month is not None and 0 <= int(beneficiary.age_month) <= 5:
        create_user_schedule(username, instance, beneficiary.beneficiary_id, "exclusive_bf")

    """
    9) Complementary Feeding schedule form will be when generated Age_month question value greater than equal to 6 and less than equal to 23
    """
    if beneficiary.age_month is not None and 6 <= int(beneficiary.age_month) <= 23:
        print('\n\n\n\n\n\n creating new schedule form... where complementary_feeding = ')
        create_user_schedule(username, instance, beneficiary.beneficiary_id, "complementary_feeding")

    """
    10) Hand Washing schedule form will be when generated Age_year question value greater than equal to 0 and less than equal to 4
    """
    if beneficiary.age_year is not None and 0 <= int(beneficiary.age_year) <= 4:
        create_user_schedule(username, instance, beneficiary.beneficiary_id, "hand_washing")

    """
    11) Pneumonia schedule form will be when generated Age_year question value greater than equal to 0 and less than equal to 4
    """
    if beneficiary.age_year is not None and 0 <= int(beneficiary.age_year) <= 4:
        create_user_schedule(username, instance, beneficiary.beneficiary_id, "pneumonia")

    """
    12) G5 Completion form will be when generated Age_year question value greater than equal to 10 and less than equal to 17
    """
    if beneficiary.age_year is not None and 10 <= int(beneficiary.age_year) <= 17:
        if beneficiary.highest_grade_passed is not None and int(beneficiary.highest_grade_passed) >= 5:
            create_user_schedule(username, instance, beneficiary.beneficiary_id, "g5_completion")

    """
    13) HIV/AIDS form will be when generated Age_year question value greater than equal to 15 and less than equal to 24
    """
    if beneficiary.age_year is not None and 15 <= int(beneficiary.age_year) <= 24:
        create_user_schedule(username, instance, beneficiary.beneficiary_id, "hiv")

    """

    class Meta:
        abstract = True

class WomenBenenficiary(Beneficiary):
    age_year = models.CharField(max_length=200)
    age_month = models.CharField(max_length=200)
    last_date_of_pregnancy = models.CharField(max_length=200)
    pregnant_lactating = models.CharField(max_length=200)
    """

