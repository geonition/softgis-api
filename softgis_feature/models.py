from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from manager import MongoDBManager
from pymongo import Connection

import datetime
import settings
import sys

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json

#this can be used instead of writing getattr everywhere
USE_MONGODB = getattr(settings, "USE_MONGODB", False)


# Create your models herelas   
# GEOMETRY MODELS
class Feature(gis_models.Model):
    """
    A Feature is defined by structure as a geojson feature
    containing a geometry object and has properties in
    the Property model.
    """
    geometry = gis_models\
                .GeometryField(srid=settings.SPATIAL_REFERENCE_SYSTEM_ID)
    user = models.ForeignKey(User)
    
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
   
class Property(models.Model):
    """
    This model saves all the properties for the features,
    """
    feature = models.ForeignKey(Feature)
    json_string = models.TextField()

    create_time = models.DateTimeField(auto_now_add=True, null=True)
    expire_time = models.DateTimeField(null=True)
    
    objects = models.Manager()
    
    if USE_MONGODB:
        mongodb = MongoDBManager(collection_name='feature_properties') #manager for querying json
    
    def save(self, *args, **kwargs):
        
        current_property = None
        current_property = \
            Property.objects.filter(feature__exact = self.feature)
        
        if current_property.count() == 0:
            #save this new property
            super(Property, self).save(*args, **kwargs)

            self.save_json_to_mongodb()
            
        else:
            current_property = current_property.latest('create_time')
            if(current_property.json_string != self.json_string):
                #delete current property
                current_property.delete()
    
                #save this new property
                super(Property, self).save(*args, **kwargs)
                
                self.save_json_to_mongodb()
                    
                
    def save_json_to_mongodb(self):
        """
        This function saves the JSON to mongodb
        """
        #do nothing if USE_MONGODB False
        if USE_MONGODB:
            insert_json = json.loads(self.json_string)
            Property.mongodb.save(insert_json, self.id)
        
        
    def delete(self, *args, **kwargs):
        self.expire_time = datetime.datetime.today()

        super(Property, self).save(*args, **kwargs)
        
        return None
    
    def __unicode__(self):
        return self.json_string