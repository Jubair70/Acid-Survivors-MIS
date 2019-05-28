from django import forms
from onadata.apps.dashboard.models import *
 

 
class DashboardControlsGeneratorForm(forms.ModelForm):
    navigation_bar = forms.ModelChoiceField(label='Tab Name', required=True, queryset=DashboardNavigationBar.objects.all(), to_field_name='id', empty_label="Select")
    cascaded_by = forms.ModelChoiceField(label='Cascaded By',required=False,
                                            queryset=DashboardControlsGenerator.objects.all(), to_field_name='id',
                                            empty_label="Select")
    class Meta:
        model = DashboardControlsGenerator
        exclude = ()



class DashboardNavigationBarForm(forms.ModelForm):
    parent_link = forms.ModelChoiceField(label='Parent Tab',required=False, queryset=DashboardNavigationBar.objects.filter(parent_link_id__isnull=True), to_field_name='id', empty_label="Select")
    link_name = forms.CharField(max_length=150, required=False)
    order = forms.IntegerField(required=False)
    class Meta:
        model = DashboardNavigationBar
        #exclude = ()



class DashboardChartDefinitionForm(forms.ModelForm):
    navigation_bar = forms.ModelChoiceField(label='Tab Name', required=True,
                                            queryset=DashboardNavigationBar.objects.filter(
                                                parent_link_id__isnull=False), to_field_name='id', empty_label="Select")
    chart_type = forms.ModelChoiceField(label='Chart Type', required=True, queryset=DashboardChartType.objects.all(), to_field_name='id', empty_label="Select")

    class Meta:
        model = DashboardGenerator


