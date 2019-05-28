from django import forms
# from django.forms import ModelForm, CharField, TextInput
from onadata.apps.unicef.models import GeoTable,GeoRMO,GeoPSU
import sys


class GeoForm(forms.ModelForm):
    # parent = forms.ModelChoiceField(label='Parent',queryset=GeoTable.objects.all(),empty_label="Select an Parent")
    class Meta:
        model = GeoTable
        fields = ('geo_id','name', 'geo_type', 'parent')


class GeoPSUForm(forms.Form):
    psu_id = forms.CharField(label="PSU ID", max_length=4)
    name = forms.CharField(label="PSU Name", max_length=150)
    geo_division = forms.ModelChoiceField(label='Division',required=True,queryset=GeoTable.objects.filter(geo_type='DV'),empty_label="Select a Division") 
    geo_district = forms.ModelChoiceField(label='District',required=True,queryset=GeoTable.objects.filter(geo_type='DC'),empty_label="Select a District") # 
    geo_upazilla = forms.ModelChoiceField(label='Upazilla',required=True,queryset=GeoTable.objects.filter(geo_type='UP'),empty_label="Select a Upazilla") # ,
    geo_union = forms.ModelChoiceField(label='Union',required=True,queryset=GeoTable.objects.filter(geo_type='UN'),empty_label="Select a Union")
    geo_rmo = forms.ModelChoiceField(label='RMO',required=True,queryset=GeoRMO.objects.all(),empty_label="Select a RMO") 
    
    def __init__(self, *args, **kwargs):
        geo_item = kwargs.pop('geo_item', None)
        super(GeoPSUForm, self).__init__(*args, **kwargs)
        if geo_item is not None:
            self.fields['psu_id'].initial = geo_item.psu_id
            self.fields['name'].initial = geo_item.name
            self.fields['geo_division'].initial = geo_item.geo_division
            self.fields['geo_district'].initial = geo_item.geo_district
            self.fields['geo_upazilla'].initial = geo_item.geo_upazilla
            self.fields['geo_union'].initial = geo_item.geo_union
            self.fields['geo_rmo'].initial = geo_item.geo_rmo
    
    def clean_psu_id(self):
        psu_id = self.cleaned_data.get('psu_id')
        try:
            psu_id = int(psu_id)
        except ValueError:
            raise forms.ValidationError('PSU Id must be an integer')
        if psu_id and len(str(psu_id)) < 4:
            raise forms.ValidationError('PSU Id must have 4 digits')
        return self.cleaned_data


class GeoRMOForm(forms.Form):
    rmo_id = forms.CharField(label="RMO ID", max_length=4)
    rmo_type = forms.CharField(label="RMO Type", max_length=100)
    
    def clean_rmo_id(self):
        rmo_id = self.cleaned_data.get('rmo_id')
        try:
            rmo_id = int(rmo_id)
        except ValueError:
            raise forms.ValidationError('RMO Id must be an integer')
        if rmo_id and len(str(rmo_id)) < 4:
            raise forms.ValidationError('RMO Id must have 4 digits')
        return self.cleaned_data