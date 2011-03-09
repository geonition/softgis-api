from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.core.exceptions import ObjectDoesNotExist
from django.utils import translation
from django.utils.encoding import smart_unicode
from django.contrib.gis.gdal import OGRGeometry
from softgis_feature.models import Feature
from softgis_feature.models import Property

import settings
import urllib2
import sys
import time
import datetime

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json

_ = translation.ugettext

USE_MONGODB = getattr(settings, "USE_MONGODB", False)

#Views for the geometry API
def feature(request):
    """
    This function handles the feature part of the softgis REST api
    
    On GET request this function returns a geojson featurecollection
    matching the query string.
    
    On POST request this function adds a new feature to the database.
    
    On PUT request this function will update a feature that has
    a given id.
    
    On DELETE request this function removes existing feature/feature collection from 
    the database.
    """
    def parse_time(time_string):
        """
        Helper function to parse a POST or GET time
        from the following format:
        yyyy-mm-dd-HH-MM-SS
        
        yyyy - year
        mm - month
        dd - day
        HH - hour
        MM - minute
        SS - second
        
        The less accurate time value have to be given before any less
        accurate time value.
        
        returns a datetime.datetime instance
        """
        time_accuracy = time_string.count('-')
        if time_accuracy == 0:
            return datetime.datetime.strptime(time_string, "%Y")
        elif time_accuracy == 1:
            return datetime.datetime.strptime(time_string, "%Y-%m")
        elif time_accuracy == 2:
            return datetime.datetime.strptime(time_string, "%Y-%m-%d")
        elif time_accuracy == 3:
            return datetime.datetime.strptime(time_string, "%Y-%m-%d-%H")
        elif time_accuracy == 4:
            return datetime.datetime.strptime(time_string, "%Y-%m-%d-%H-%M")
        elif time_accuracy == 5:
            return datetime.datetime.strptime(time_string, "%Y-%m-%d-%H-%M-%S")
    
    if request.method  == "GET":
        
        # get the definied limiting parameters
        limiting_param = request.GET.items()
        
        feature_collection = {"type":"FeatureCollection", "features": []}
        
        feature_queryset = None

        #filter according to permissions
        if(request.user.has_perm('softgis_api.can_view_all')):
            feature_queryset = Feature.objects.all()

        elif(request.user.is_authenticated()):
            #else the user can only view his/her own features
            feature_queryset = \
                    Feature.objects.filter(user__exact = request.user)
        else:
            feature_queryset = Feature.objects.none()

        property_queryset = Property.objects.all()
        mongo_query = {}
        
        #filter according to limiting_params
        for key, value in limiting_param:
            if(key == "user_id"):
                feature_queryset.filter(user__exact = value)
            
            elif(key == "create_time__lt"):
                dt = parse_time(value)
                feature_queryset.filter(create_time__lt = dt)
                property_queryset.filter(create_time__lt = dt)
                
            elif(key == "create_time__gt"):
                dt = parse_time(value)
                feature_queryset.filter(create_time__gt = dt)
                property_queryset.filter(create_time__gt = dt)
                
            elif(key == "create_time__latest" and value == "true"):
                feature_queryset.latest('create_time')
                property_queryset.latest('create_time')
                print feature_queryset
            
            elif(key == "expire_time__lt"):
                dt = parse_time(value)
                feature_queryset.filter(expire_time__lt = dt)
                property_queryset.filter(expire_time__lt = dt)
            
            elif(key == "expire_time__gt"):
                dt = parse_time(value)
                feature_queryset.filter(expire_time__gt = dt)
                property_queryset.filter(expire_time__gt = dt)
                
            elif(key == "expire_time__latest" and value == "true"):
                feature_queryset.latest('expire_time')
                property_queryset.latest('expire_time')
            
            #mongodb queries should be built here
            elif USE_MONGODB:
                key = str(key)
                if value.isnumeric():
                    value = int(value)
                elif value == "true":
                    value = True
                elif value == "false":
                    value = False
                    
                mongo_query[key] = value
        
        #filter the features with wrong properties, and add the result to the
        #id set
        feature_id_set = set()
        feature_id_set = feature_id_set.union(set(property_queryset.values_list('feature_id', flat=True)))
        
        #filter the queries acccording to the json
        if len(mongo_query) > 0:
            #connect to collection,,
            Property.mongodb.connect(Property.mongodb_collection_name)
            qs = Property.mongodb.find(mongo_query)
            Property.mongodb.disconnect()
            feature_id_set = feature_id_set.intersection(set(qs.values_list('feature_id', flat=True)))
        

        # gives database error in sqlite3 ?
        feature_queryset = feature_queryset.filter(id__in = list(feature_id_set))
        
        for feature in feature_queryset:
            feature_collection['features'].append(feature.geojson())

        # According to GeoJSON specification crs member
        # should be on the top-level GeoJSON object
        # get srid from the first feature in the collection
        if feature_queryset.exists():
            srid = feature_queryset[0].geometry.srid
        else:
            srid = 3067

        crs_object =  {"type": "EPSG", "properties": {"code": srid}}
        feature_collection['crs'] = crs_object
        
        return HttpResponse(json.dumps(feature_collection),
                            mimetype="application/json")
        
            
    elif request.method == "POST":
        #supports saving geojson Features
        feature_json = json.loads(request.POST.keys()[0])
        geojson_type = None
        
        try:
            geojson_type = feature_json['type']
        except KeyError:
            return HttpResponseBadRequest(_("geojson did not inclue a type." + \
                                          " Accepted types are " + \
                                          "'FeatureCollection' and 'Feature'."))
        
        #inner function to save one feature
        if geojson_type == "Feature":
            geometry = None
            properties = None
            try:
                geometry = feature_json['geometry']
                properties = feature_json['properties']
            except KeyError:
                return HttpResponseBadRequest("geojson type 'Feature' " + \
                                            "requires properties "  + \
                                            "and geometry")
                
                
            #geos = GEOSGeometry(json.dumps(geometry))
            # Have to make OGRGeometry as GEOSGeometry
            # does not support spatial reference systems
            geos = OGRGeometry(json.dumps(geometry)).geos
            
            #save the feature
            new_feature = Feature(geometry=geos,
                                user=request.user)
            new_feature.save()
    
            #add the id to the feature json
            identifier = new_feature.id
            feature_json['id'] = identifier
    
            #save the properties of the new feature
            new_property = Property(feature=new_feature,
                                    json_string=json.dumps(properties))
            new_property.save()
                
            return HttpResponse(json.dumps(feature_json))
            
        elif geojson_type == "FeatureCollection":
            features = feature_json['features']
            ret_featurecollection = {
                "type": "FeatureCollection",
                "features": []
            }
            
            for feat in features:
                geometry = None
                properties = None
                try:
                    geometry = feat['geometry']
                    properties = feat['properties']
                except KeyError:
                    return HttpResponseBadRequest("geojson type 'Feature' " + \
                                                "requires properties "  + \
                                                "and geometry in " + \
                                                "FeatureCollection")
                
                
                #geos = GEOSGeometry(json.dumps(geometry))
                # Have to make OGRGeometry as GEOSGeometry
                # does not support spatial reference systems
                geos = OGRGeometry(json.dumps(geometry)).geos
            
                #save the feature
                new_feature = Feature(geometry=geos,
                                    user=request.user)
                new_feature.save()
    
                #add the id to the feature json
                identifier = new_feature.id
                feat['id'] = identifier
    
                #save the properties of the new feature
                new_property = Property(feature=new_feature,
                                        json_string=json.dumps(properties))
                new_property.save()
                
                ret_featurecollection['features'].append(feat)
                
            return HttpResponse(json.dumps(ret_featurecollection))
            
    elif request.method == "PUT":
        
        #supports updating geojson Features
        feature_json = json.loads(urllib2.unquote(request.raw_post_data.encode('utf-8')).decode('utf-8'))
        geometry = None
        properties = None
        feature_id = None
        
        try:
            geojson_type = feature_json['type']
        except KeyError:
            return HttpResponseBadRequest(_("geojson did not inclue a type." + \
                                          " Accepted types are " + \
                                          "'FeatureCollection' and 'Feature'."))
        if geojson_type == "Feature":
            
            try:
                geometry = feature_json['geometry']
                properties = feature_json['properties']
                feature_id = feature_json['id']
            except KeyError:
                return HttpResponseBadRequest("geojson feature requires " + \
                                            "properties, "  + \
                                            "geometry " + \
                                            "and id for updating")
                
            #geos = GEOSGeometry(json.dumps(geometry))
            # Have to make OGRGeometry as GEOSGeometry
            # does not support spatial reference systems
            geos = OGRGeometry(json.dumps(geometry)).geos
            
            #get the feature to be updated
            feature_queryset = Feature.objects.filter(id__exact = feature_id,
                                                    user__exact = request.user)
            
            if len(feature_queryset) == 1:
                feature = feature_queryset[0]
                feature.geos = geos;
                feature.save()
                
                #save the properties of the new feature
                new_property = Property(feature=feature,
                                        json_string=json.dumps(properties))
                new_property.save()
                
                return HttpResponse(_(u"Feature with id %s was updated" % feature_id))
            else:
                return HttpResponseNotFound(_(u"Feature with id %s was not found" % feature_id))
        
        elif geojson_type == "FeatureCollection":
                
            features = feature_json['features']
            
            for feat in features:  
            
                try:
                    geometry = feat['geometry']
                    properties = feat['properties']
                    feature_id = feat['id']
                except KeyError:
                    return HttpResponseBadRequest("geojson feature requires " + \
                                                "properties, "  + \
                                                "geometry " + \
                                                "and id for updating")
                
                #geos = GEOSGeometry(json.dumps(geometry))
                # Have to make OGRGeometry as GEOSGeometry
                # does not support spatial reference systems
                geos = OGRGeometry(json.dumps(geometry)).geos
                
                #get the feature to be updated
                feature_queryset = Feature.objects.filter(id__exact = feature_id,
                                                        user__exact = request.user)
                
                if len(feature_queryset) == 1:
                    feature = feature_queryset[0]
                    feature.geos = geos;
                    feature.save()
                    
                    #save the properties of the new feature
                    new_property = Property(feature=feature,
                                            json_string=json.dumps(properties))
                    new_property.save()
                else:
                    return HttpResponseNotFound(_(u"Feature with id %s was not found" % feature_id))
                    
            
            return HttpResponse(_(u"Features updated"))
                    
    elif request.method  == "DELETE":

        """
        Get the array with the feature ids for delete
        """
        feature_ids = json.loads(request.GET.get("ids","[]"))
        

        if (type(feature_ids) != type([])):
            return HttpResponseBadRequest(_(u"The post request didn't have an array of ids"))

        feature_queryset = Feature.objects.filter(id__in = feature_ids,
                                                user__exact = request.user)

        if len(feature_queryset) > 0:
            feature_queryset.delete()
            return HttpResponse(_(u"Features with ids %s deleted" % feature_ids))
        else:
            return HttpResponseNotFound(_(u"Features with given ids were not found"))
