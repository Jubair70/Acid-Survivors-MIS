from django.db import models


class GeoPsu(models.Model):
    geo_division_id = models.CharField(max_length=200)
    geo_district_id = models.CharField(max_length=200)
    geo_upazilla_id = models.CharField(max_length=200)
    geo_union_id = models.CharField(max_length=200)
    geo_mauza_id = models.CharField(max_length=200)
    geo_village_id = models.CharField(max_length=200)
    geo_psu_id = models.CharField(max_length=200)
    user_id = models.CharField(max_length=200)

class Meta:
    app_label = 'scheduling'
