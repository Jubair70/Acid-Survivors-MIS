from django.db import models
from django.contrib.auth.models import User


class GeoTable(models.Model):
    NA= 'NA'
    DIVISION = 'DV'
    DISTRICT = 'DC'
    UPAZILLA = 'UP'
    UNION = 'UN'
    VILLAGE = 'VL'
    TYPES = (
        (NA, 'Select a Type'),
        (DIVISION, 'Division'),
        (DISTRICT, 'District'),
        (UPAZILLA, 'Upazilla'),
        (UNION , 'Union'),
        (VILLAGE , 'Village'),
    )
    geo_id = models.IntegerField()
    name = models.CharField(max_length=150)
    parent = models.ForeignKey('GeoTable',related_name='geo_table_parent', on_delete=models.CASCADE,blank=True,null=True)
    geo_type =  models.CharField(max_length=2,
                                      choices=TYPES,
                                      default=NA)
    # Override the __unicode__() method to return out something meaningful!
    def __str__(self):
        return self.name


class GeoPSU(models.Model):
    # user = models.ManyToManyField(User)
    psu_id = models.IntegerField()
    name = models.CharField(max_length=150)
    geo_district = models.ForeignKey('GeoTable',related_name='geo_district', on_delete=models.CASCADE,limit_choices_to={'geo_type': 'DC'},)
    geo_division = models.ForeignKey('GeoTable',related_name='geo_division', on_delete=models.CASCADE,limit_choices_to={'geo_type': 'DV'},)
    geo_upazilla = models.ForeignKey('GeoTable',related_name='geo_upazilla', on_delete=models.CASCADE,limit_choices_to={'geo_type': 'UP'},)
    geo_union = models.ForeignKey('GeoTable',related_name='geo_union', on_delete=models.CASCADE,limit_choices_to={'geo_type': 'UN'},)
    geo_rmo = models.ForeignKey('GeoRMO',related_name='geo_rmo', on_delete=models.CASCADE)
    # Override the __unicode__() method to return out something meaningful!
    def __str__(self):
        return self.name


class GeoRMO(models.Model):
    rmo_id = models.IntegerField(unique=True)
    rmo_type = models.CharField(max_length=150)
    
    def __str__(self):
        return str(self.rmo_id)
