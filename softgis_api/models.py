# -*- coding: utf-8 -*-
"""
This file contains all the models for the api
"""
from django.db import models
from django.utils import translation
from django.contrib.auth.models import User
from django.contrib.gis.db import models as gis_models
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save
from django.core.signals import request_finished
from django.db import IntegrityError

import django
import settings
import datetime

import sys

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json

if settings.USE_MONGODB:
    from pymongo import Connection

_ = translation.ugettext
    

class StaticProfileValue(models.Model):
    """
    This model contains all the information of a user that
    is not dynamic. Meaning that it does not changes during
    a persons lifetime.
    """
    user = models.OneToOneField(User)
    #add here static profile values for each user
    allow_notifications = models.BooleanField(default=False)

    GENDER_CHOICES = (('M', 'Male'), ('F', 'Female'), )
    gender = models.CharField(blank=True,
                              null=True,
                              max_length = 1,
                              choices = GENDER_CHOICES)

    BIRTHYEAR_CHOICES = ()
    years = range(datetime.date.today().year - 100,
                  datetime.date.today().year - 5)
    for year in years:
        BIRTHYEAR_CHOICES = BIRTHYEAR_CHOICES + ((year, year),)
        
    birthyear = models.IntegerField(blank=True,
                                    null=True,
                                    choices = BIRTHYEAR_CHOICES)

    email = models.EmailField(blank=True,
                              null=True)
    email_confirmed = models.BooleanField(default=False)


#signal handler for profile creation
#def profile_handler(sender, instance, created, **kwargs):
    """
    This function makes sure that the extension profile values
    the StaticProfileValue is created for each user.

    it is connected to the post_save() signal of the user model
    """
 #   print sender
  #  print instance
 #   print created
 #   if created == True:
 #       try:
            #associate_profile = StaticProfileValue(user=instance)
            #associate_profile.save()
 #           pass
 #       except IntegrityError:
            #django.db.connection.close()
 #           pass

#post_save.connect(profile_handler, sender=User)

class ProfileValue(models.Model):
    """
    additional possibly changing values to connect to
    a Persons profile
    """
    user = models.ForeignKey(User)
    json_string = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)
    expire_time = models.DateTimeField(null=True)
    
    def save(self, *args, **kwargs):
        """
        This function saves the new profile value and marks the old profile
        values as expired.
        """
        current_value = None
        current_value = \
            ProfileValue.objects.filter(user__exact = self.user)

        if(current_value.count() == 0):
            
            super(ProfileValue, self).save(*args, **kwargs)

            if(settings.USE_MONGODB):
                self.save_json_to_mongodb()
       
        else:
            current_value = current_value.latest('create_time')

            if(current_value.json_string == self.json_string):
                pass
            else:
                current_value.delete()

                super(ProfileValue, self).save(*args, **kwargs)
                
                if(settings.USE_MONGODB):
                    self.save_json_to_mongodb()

    def save_json_to_mongodb(self):
        """
        This function saves the JSON to the mongodb
        """
        insert_json = json.loads(self.json_string)
        insert_json['profile_id'] = int(self.id)
       
        con = Connection()
        
        db = con.softgis
        profiles = db.profiles
        obj_id = profiles.insert(insert_json)

        con.disconnect()

    def delete(self, *args, **kwargs):
        """
        This function sets the current profile value as
        expired
        """
        
        self.expire_time = datetime.datetime.today()
        super(ProfileValue, self).save(*args, **kwargs)
        
        return None

    def __unicode__(self):
        return self.json_string
        
    class Meta:
        get_latest_by = 'create_time'
        ordering = ['-create_time', 'user']
        permissions = (
            ("can_view_profiles", "can view profiles"),)
        unique_together = (("expire_time", "json_string", "user"),)


def get_user_profile(user):
    """
    returns a dictionary object of the given
    users profile
    """
    if not user.is_authenticated():
        return {}

    profile_dict = {}
    try:
        profile = ProfileValue.objects.filter(user__exact = user)\
                                      .latest('create_time')

        profile_dict = json.loads(profile.json_string)
    except ObjectDoesNotExist:
        pass

    try:
        profile_dict['allow_notifications'] = StaticProfileValue.objects\
                                                .get(user__exact = user)\
                                                .allow_notifications
        profile_dict['gender'] = StaticProfileValue.objects\
                                            .get(user__exact = user)\
                                            .gender
        profile_dict['email'] = StaticProfileValue.objects\
                                            .get(user__exact = user)\
                                            .email
        profile_dict['birthyear'] = StaticProfileValue.objects\
                                            .get(user__exact = user)\
                                            .birthyear
    except ObjectDoesNotExist:
        pass
    
    return profile_dict

    
def get_profiles(limit_param, profile_queryset):
    """
    Returns a list of profiles that fits the limiting param and
    is in the given profile_queryset
    """
    if(profile_queryset == None):
        profile_queryset = ProfileValue.objects.all()

    profile_id_list = list(profile_queryset.values_list('id', flat=True))

    #open connection to mongodb
    con = None
    db = None
    profiles = None

    if(settings.USE_MONGODB):
        con = Connection()
        db = con.softgis
        profiles = db.profiles
    
    for key, value in limit_param:
        if(key == "user_id"):
            profile_queryset = profile_queryset.filter(user__exact = value)

        elif(key == "latest" and value == "true"):
            profile_queryset = profile_queryset.filter(expire_time__isnull=True)

        elif(settings.USE_MONGODB):

            try:
                value_name = key.split("__")[0]
                query_type = key.split("__")[1]
            except IndexError:
                query_type = None

            if(query_type == None):

                profile_ids = []
                for profile in profiles.find({key: value,
                                            "profile_id":
                                            {"$in": profile_id_list}}):
                                                
                    profile_ids.append(profile['profile_id'])

                profile_queryset = profile_queryset.filter(id__in = profile_ids)
                
            elif(query_type == "range"):
                min = value.split("-")[0]
                max = value.split("-")[1]

                profile_ids = []
                
                for profile in profiles.find({value_name: {"$lte": max,
                                                           "$gte": min},
                                            "profile_id": {"$in":
                                                           profile_id_list}}):
                                                               
                    profile_ids.append(profile['profile_id'])
                    
                profile_queryset = profile_queryset.filter(id__in = profile_ids)
                

    #close connection to mongodb
    if(settings.USE_MONGODB):
        con.disconnect()
    
    profile_list = []
    
    for profile in profile_queryset:
        profile_dict = json.loads(profile.json_string)
        profile_dict['allow_notifications'] = profile\
                                                .user\
                                                .staticprofilevalue\
                                                .allow_notifications
        profile_list.append(profile_dict)

    return profile_list
   
#GEOMETRY MODELS
class Feature(gis_models.Model):
    """
    A Feature is defined by structure as a geojson feature
    containing a geometry object and has properties in
    the Property model.
    """
    geometry = gis_models\
                .GeometryField(srid=settings.SPATIAL_REFERENCE_SYSTEM_ID)
    user = models.ForeignKey(User)
    category = models.CharField(max_length=100)
    
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    expire_time = models.DateTimeField(null=True)
    
    objects = gis_models.GeoManager()
    
    def delete(self, *args, **kwargs):
        self.expire_time = datetime.datetime.today()
        
        return None
    
    def geojson(self):

        properties = None
        properties_dict = None
        
        try:
            # this should be changed to support different time queries
            properties = Property.objects.filter(feature__exact=self)\
                                            .latest('create_time')
            properties_dict = json.loads(properties.json_string)
        except ObjectDoesNotExist:
            properties_dict = {}
            
        feature_json = {}
        
        #set the default property values
        properties_dict['id'] = self.id
        properties_dict['user_id'] = self.user.id
        
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

            ("can_view_non_confidential",
            "Can view the non confidential features"),)


def get_user_features(user):

    feature_collection = {"type":"FeatureCollection", "features": []}

    if not user.is_authenticated():
        return feature_collection
        
    feature_queryset = Feature.objects.filter(user__exact = user,
                                              expire_time__isnull = True)

    for feature in feature_queryset:
        feature_collection['features'].append(feature.geojson())

    # According to GeoJSON specification crs member should be on the
    # top-level GeoJSON object get srid from the first feature in the collection
    if feature_queryset.exists():
        srid = feature_queryset[0].geometry.srid
    else:
        srid = 3067
        
    crs_object =  {"type": "EPSG", "properties": {"code": srid}}
    feature_collection['crs'] = crs_object

    return feature_collection

def get_features(limit_param, feature_queryset):
    """
    This method returns a list of features that fits the limiting param
    and is from th given feature_queryset
    """
    if(feature_queryset == None):
        feature_queryset = Feature.objects.all()

    feature_id_list = feature_queryset.values_list('id', flat=True)

    #open connection to mongodb
    con = None
    db = None
    feature_properties = None

    if(settings.USE_MONGODB):
        con = Connection()
        db = con.softgis
        feature_properties = db.feature_properties
    

    for key, value in limit_param:
        if(settings.USE_MONGODB):
            try:
                value_name = key.split("__")[0]
                query_type = key.split("__")[1]
            except IndexError:
                query_type = None

            if(query_type == None):

                feature_ids = []
                
                for feature_property in feature_properties.find({key:value,
                                                                "feature_id":
                                                                {"$in":
                                                                feature_id_list
                                                                }}):
                                                                    
                    feature_ids.append(feature_property['feature_id'])

                feature_queryset = feature_queryset.filter(id__in = feature_ids)
                

    #close connection to mongodb
    if(settings.USE_MONGODB):
        con.disconnect()

    feature_list = []

    for feature in feature_queryset:
        feature_list.append(json.loads(feature.json_string))
        
    return feature_list

   
class Property(models.Model):
    """
    This model saves all the properties for the features,
    """
    feature = models.ForeignKey(Feature)
    json_string = models.TextField()

    create_time = models.DateTimeField(auto_now_add=True, null=True)
    expire_time = models.DateTimeField(null=True)
    
    def save(self, *args, **kwargs):
        
        current_property = None
        current_property = \
            Property.objects.filter(feature__exact = self.feature)
        
        if current_property.count() == 0:
            super(Property, self).save(*args, **kwargs)

            if(settings.USE_MONGODB):
                self.save_json_to_mongodb()
            
        else:
            current_property = current_property.latest('create_time')
            
            if(current_property.json_string == self.json_string):
                pass
            else:
                current_property.delete()

                super(Property, self).save(*args, **kwargs)

                if(settings.USE_MONGODB):
                    self.save_json_to_mongodb()
                
    def save_json_to_mongodb(self):
        """
        This function saves the JSON to the mongodb
        """
        insert_json = json.loads(self.json_string)
        insert_json['feature_id'] = int(self.feature.id)
        insert_json['property_id'] = int(self.id)

        con = Connection()
        db = con.softgis
        feature_properties = db.feature_properties
        obj_id = feature_properties.insert(insert_json)

        con.disconnect()
        
        
    def delete(self, *args, **kwargs):
        self.expire_time = datetime.datetime.today()

        super(Property, self).save(*args, **kwargs)
        
        return None
    
    def __unicode__(self):
        return self.json_string
