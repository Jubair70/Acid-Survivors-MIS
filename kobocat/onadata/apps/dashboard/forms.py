from onadata.apps.dashboard.models import *
from django import forms


class DashboardLoaderUpdateForm(forms.ModelForm):
    class Meta:
        model = DashboardLoader
        exclude = ()

