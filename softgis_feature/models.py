from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


import settings

import sys

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json

# Create your models here.

   
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