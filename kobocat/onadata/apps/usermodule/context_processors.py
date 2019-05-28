from django.conf import settings
from django.contrib.sites.models import Site
from onadata.apps.usermodule.models import MenuItem,UserModuleProfile
from onadata.apps.usermodule.models import MenuRoleMap,UserRoleMap
import sys 

def site_name(request):
    site_id = getattr(settings, 'SITE_ID', None)
    try:
        site = Site.objects.get(pk=site_id)
    except Site.DoesNotExist:
        site_name = 'example.org'
    else:
        site_name = site.name
    return {'SITE_NAME': site_name}


def additional_menu_items(request):
    user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
    menu_items = []
    sub_menu_items = []
    if not request.user.id == None:
        current_user = UserModuleProfile.objects.filter(user=request.user)
        if current_user:
            current_user = current_user[0]
            if request.user.is_superuser:
                menu_items = MenuItem.objects.exclude(parent_menu__isnull=False)
                sub_menu_items = MenuItem.objects.exclude(parent_menu__isnull=True)
            else:
                admin_menu = 0
                roles_list = UserRoleMap.objects.filter(user=current_user).values('role')
                for role in roles_list:
                    alist = MenuRoleMap.objects.filter(role=role['role']).values('menu')
                    mist = []
                    for i in alist:
                        mist.append( i['menu'])
                    role_menu_list = MenuItem.objects.filter(pk__in=mist).exclude(parent_menu__isnull=False)
                    role_submenu_list = MenuItem.objects.filter(pk__in=mist).exclude(parent_menu__isnull=True)
                    menu_items.extend(role_menu_list)
                    sub_menu_items.extend(role_submenu_list)
        else:
            menu_items = MenuItem.objects.exclude(parent_menu__isnull=False)
            sub_menu_items = MenuItem.objects.exclude(parent_menu__isnull=True)

    menu_items = list(set(menu_items))
    menu_items = sorted(menu_items, key=lambda x: x.sort_order)
    sub_menu_items = list(set(sub_menu_items))
    sub_menu_items = sorted(sub_menu_items, key=lambda x: x.sort_order)
    return {'main_menu_items': menu_items, 'sub_menu_items':sub_menu_items}


def is_admin(request):
    admin_menu = 0
    user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
    if not user.is_anonymous():
        current_user = UserModuleProfile.objects.filter(user=user)
        if current_user:
            current_user = current_user[0]
            if current_user.admin:
                admin_menu = 1
            else:
                admin_menu = 0
        else:
            admin_menu = 1   
    return {'admin_menu': admin_menu}

def care_viewer(request):
    admin_menu = 0
    care_usa = 0
    care_bd = 0
    care_np = 0
    kobo_priv = 0
    user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
    
    # print user.username
    if not user.is_anonymous():
        current_user = UserModuleProfile.objects.filter(user=user).first()
        if current_user:
            organization =  current_user.organisation_name.organization
            # current_user = current_user[0]
            if organization == 'CARE Nepal':
                care_np = 1
            if organization == 'CARE Bangladesh':
                care_bd = 1
        else:
            care_usa = 1 
            kobo_priv = 1  
    return {'care_np': care_np,
    'care_bd':care_bd,
    'care_usa':care_usa,
    'kobo_priv':kobo_priv}
    
