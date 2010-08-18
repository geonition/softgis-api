# -*- coding: utf-8 -*-
"""
This file contains all the models for the api
"""
from django.db import models
from django.utils import translation
from django.contrib.auth.models import User
from django.contrib.gis.db import models as gis_models
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.utils.encoding import smart_unicode

import datetime

import sys

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json

_ = translation.ugettext
    
    
class ProfileValue(models.Model):
    """
    additional possibly changing values to connect to
    a Person
    """
    user = models.ForeignKey(User)
    value_name = models.CharField(max_length=18)
    value = models.CharField(max_length=100)
    create_time = models.DateTimeField(auto_now_add=True)
    expire_time = models.DateTimeField(null=True)
    
    def save(self, *args, **kwargs):
        current_value = None
        current_value = \
            ProfileValue.objects.filter(value_name__exact = self.value_name, \
                                    user__exact = self.user, \
                                    expire_time__isnull = True)
        
        if current_value.count() == 0:
            super(ProfileValue, self).save(*args, **kwargs)
        
        elif current_value[0].value_name == smart_unicode(self.value_name, \
            encoding='utf-8') and current_value[0].value == \
            smart_unicode(self.value,encoding='utf-8'):
            pass
            
        else:
            current_value[0].delete()
            
            super(ProfileValue, self).save(*args, **kwargs)
            
    def delete(self, *args, **kwargs):
        self.expire_time = datetime.datetime.today()
        
        super(ProfileValue, self).save(*args, **kwargs)
        
        return None
            
    def __unicode__(self):
        return str(self.value_name) + " = " + str(self.value)
        
    class Meta:
        get_latest_by = 'create_time'
        ordering = ['-create_time', 'user']
        permissions = (
            ("can_view_profiles", "can view profiles"),)
        unique_together = (("expire_time", "value_name", "user"),)

def get_profile(user):
    """
    returns a dictionary object of the given
    users profile value_name value pairs
    """
    if not user.is_authenticated():
        return {}
        
    profile_queryset = \
        ProfileValue.objects.filter(user__exact = user)\
                            .order_by('create_time')
                            
    profile_dict = {}
    for profile_value in profile_queryset:
        value_name = profile_value.value_name
        value = profile_value.value

        try:
            profile_dict[value_name] = eval(value)
        except:
            profile_dict[value_name] = value
            
    return profile_dict
   
#GEOMETRY MODELS   
    
class Feature(gis_models.Model):
    """
    A Feature is defined by structure as a geojson feature
    containing a geometry object and has properties in
    the Property model.
    """
    geometry = gis_models.GeometryField()
    user = models.ForeignKey(User)
    category = models.CharField(max_length=100)
    
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    expire_time = models.DateTimeField(null=True)
    
    objects = gis_models.GeoManager()
    
    def delete(self, *args, **kwargs):
        self.expire_time = datetime.datetime.today()
        
        return None
    
    def geojson(self, profile=False):
    
        properties = Property.objects\
                                    .filter(feature__exact=self, \
                                            expire_time__isnull = True)
        properties_dict = {}
        profile_dict = {}
        feature_json = {}
        
        #set the default property values
        properties_dict['id'] = self.id;
        properties_dict['user_id'] = self.user.id
        
        for prop in properties:
            try:
                properties_dict[prop.value_name] = eval(prop.value)
            except:
                properties_dict[prop.value_name] = prop.value
        
        if profile:
            profile = ProfileValue.objects\
                                        .filter(user__exact = self.user)
                                        
            for val in profile:
                try:
                    profile_dict[val.value_name] = eval(val.value)
                except:
                    profile_dict[val.value_name] = val.value
        
            properties_dict.update(profile_dict)
            
            feature_json = {"id": self.id,
                            "geometry": json.loads(self.geometry.json),
                            "properties": properties_dict}
            
        else:
            feature_json = {"id": self.id,
                            "geometry": json.loads(self.geometry.json),
                            "properties": properties_dict}
        
        return feature_json
    
    def __unicode__(self):
        feature_json = self.geojson()
        
        return str(feature_json)
        
        
    class Meta:
        permissions = (
            ("can_view_all", "Can view all features"),
            ("can_view_non_confidential", "Can view the non confidential features"),)


def get_features(user, property_query=""):

    feature_collection = {"type":"FeatureCollection", "features": []}

    if not user.is_authenticated():
        return feature_collection
        
    feature_queryset = Feature.objects.filter(user__exact = user)

    for feature in feature_queryset:
        feature_collection['features'].append(feature.geojson())

    return feature_collection
    
   
class Property(models.Model):
    """
    This model saves all the properties for the features,
    """
    feature = models.ForeignKey(Feature)
    value_name = models.CharField(max_length=30)
    value = models.TextField()

    create_time = models.DateTimeField(auto_now_add=True, null=True)
    expire_time = models.DateTimeField(null=True)
    
    def save(self, *args, **kwargs):
        
        current_property = None
        current_property = \
            Property.objects.filter(value_name__exact = self.value_name, \
                                    feature__exact = self.feature, \
                                    expire_time__isnull = True)
        
        if current_property.count() == 0:
            super(Property, self).save(*args, **kwargs)
        
        elif current_property[0].value_name == self.value_name and \
            current_property[0].value == self.value:
            pass
            
        else:
            current_property.update(expire_time = datetime.datetime.today())
            
            super(Property, self).save(*args, **kwargs)    
    
    def delete(self, *args, **kwargs):
        self.expire_time = datetime.datetime.today()
        
        return None
    
    def __unicode__(self):
        ret_val = self.value_name + " = " + self.value
        return ret_val
