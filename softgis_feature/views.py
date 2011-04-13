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
from HttpResponseExtenders import HttpResponseNotAuthorized

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
        or None if format was wrong
        """
        if sys.version_info >= (2, 6): #remove this when django drops support for 2.4
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
        else:
            time_accuracy = time_string.count('-')
            time_split = time_string.split('-')
            if time_accuracy == 0:
                return datetime.datetime(int(time_split[0]))
            elif time_accuracy == 1:
                return datetime.datetime(int(time_split[0]),
                                         int(time_split[1]))
            elif time_accuracy == 2:
                return datetime.datetime(int(time_split[0]),
                                         int(time_split[1]),
                                         int(time_split[2]))
            elif time_accuracy == 3:
                return datetime.datetime(int(time_split[0]),
                                         int(time_split[1]),
                                         int(time_split[2]),
                                         int(time_split[3]))
            elif time_accuracy == 4:
                return datetime.datetime(int(time_split[0]),
                                         int(time_split[1]),
                                         int(time_split[2]),
                                         int(time_split[3]),
                                         int(time_split[4]))
            elif time_accuracy == 5:
                return datetime.datetime(int(time_split[0]),
                                         int(time_split[1]),
                                         int(time_split[2]),
                                         int(time_split[3]),
                                         int(time_split[4]),
                                         int(time_split[5]))
    

    #print request
    if not request.user.is_authenticated():
        return HttpResponseNotAuthorized(_("You need to login or create a session in order to manipulate features"))    

    if request.method  == "GET":
        
        #print request.user
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
            
            key = str(key)
            if value.isnumeric():
                value = int(value)
            elif value == "true":
                value = True
            elif value == "false":
                value = False
                
            key_split = key.split('__')
            command = ""
            
            if len(key_split) > 1:
                key = key_split[0]
                command = key_split[1]
            
            if(key == "user_id"):
                feature_queryset = feature_queryset.filter(user__exact = value)
                
            elif(key == "id"):
                feature_queryset = feature_queryset.filter(id__exact = value)
            
            elif(key == "time"):
                
                dt = None
                 
                if(command == "now" and value):
                    dt = datetime.datetime.now()
                elif(command == "now" and not value):
                    continue
                else:
                    dt = parse_time(value)
                
                property_qs_expired = property_queryset.filter(create_time__lte = dt)
                property_qs_expired = property_qs_expired.filter(expire_time__gte = dt)
                    
                property_qs_not_exp = property_queryset.filter(create_time__lte = dt)
                property_qs_not_exp = property_qs_not_exp.filter(expire_time = None)
                property_qs_not_exp = property_qs_not_exp.exclude(id__in = property_qs_expired)
                    
                property_queryset = property_qs_not_exp | property_qs_expired
                    
                #do the same for features
                feature_ids = property_queryset.values_list('feature_id', )
                feature_queryset = feature_queryset.filter(id__in = feature_ids)
                feature_qs_expired = feature_queryset.filter(expire_time__gt = dt)
                feature_qs_expired = feature_qs_expired.filter(create_time__lt = dt)
                feature_qs_not_expired = feature_queryset.filter(expire_time = None)
                feature_queryset = feature_qs_not_expired | feature_qs_expired 
                
            #mongodb queries should be built here
            elif USE_MONGODB:
                
                if command == "max":

                    if mongo_query.has_key(key):
                        mongo_query[key]["$lte"] = value
                    else:
                        mongo_query[key] = {}
                        mongo_query[key]["$lte"] = value
                        
                elif command == "min":

                    if mongo_query.has_key(key):
                        mongo_query[key]["$gte"] = value
                    else:
                        mongo_query[key] = {}
                        mongo_query[key]["$gte"] = value

                elif command == "":
                    mongo_query[key] = value
        
                
        #filter the queries acccording to the json
        if len(mongo_query) > 0:
            mongo_query['_id'] = {"$in": list(property_queryset.values_list('id', flat=True))}
            qs = Property.mongodb.find(mongo_query)
            property_queryset = property_queryset.filter(id__in = qs.values_list('id', flat=True))
        
        #filter the properties not belonging to feature_queryset
        property_queryset = property_queryset.filter(feature__in = feature_queryset)
        
        for prop in property_queryset:
            feature_collection['features'].append(prop.geojson())

        # According to GeoJSON specification crs member
        # should be on the top-level GeoJSON object
        # get srid from the first feature in the collection
        if property_queryset.exists():
            srid = property_queryset[0].feature.geometry.srid
        else:
            srid = getattr(settings, "SPATIAL_REFERENCE_SYSTEM_ID", 4326)

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
                feat['id'] = int(identifier)
                
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
             
            #get the feature to be updated
            feature_old = None
            try:
                feature_old = Feature.objects.get(id__exact = feature_id)
            except ObjectDoesNotExist:
                return HttpResponseNotFound("The feature with id %i was not found" % feature_id)
            
            if feature_old.user != request.user:
                return HttpResponseForbidden("You do not have permission to" + \
                                             " update feature %i" % feature_id)   
            
            
            #geos = GEOSGeometry(json.dumps(geometry))
            # Have to make OGRGeometry as GEOSGeometry
            # does not support spatial reference systems
            geos = OGRGeometry(json.dumps(geometry)).geos
            
            feature = feature_old.update(geometry = geos)
            
            #save the properties of the new feature
            cur_property = Property.objects\
                            .filter(feature = feature_old)\
                            .latest('create_time')
            
            if feature_old.id == feature.id: #if there was nothing updated
                new_property = cur_property.update(json.dumps(properties))
            else: #feature was updated so new property created
                cur_property.delete()
                new_property = Property(feature=feature,
                                    json_string=json.dumps(properties))
                new_property.save()
            
            return HttpResponse(_(u"Feature with id %s was updated" % feature_id))
    
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
             
                #get the feature to be updated
                feature_old = None
                try:
                    feature_old = Feature.objects.get(id__exact = feature_id)
                except DoesNotExist:
                    return HttpResponseNotFound("The feature with id %i was not " +\
                                                "found" % feature_id)
                
                if feature_old.user != request.user:
                    return HttpResponseForbidden("You do not have permission to" + \
                                                 " update feature %i" % feature_id)   
                
                
                #geos = GEOSGeometry(json.dumps(geometry))
                # Have to make OGRGeometry as GEOSGeometry
                # does not support spatial reference systems
                geos = OGRGeometry(json.dumps(geometry)).geos
                
                feature = feature_old.update(geometry = geos)
                
                #save the properties of the new feature
                cur_property = Property.objects\
                                .filter(feature = feature_old)\
                                .latest('create_time')
                
                if feature_old.id == feature.id: #if there was nothing updated
                    new_property = cur_property.update(json.dumps(properties))
                else: #feature was updated so new property created
                    cur_property.delete()
                    new_property = Property(feature=feature,
                                        json_string=json.dumps(properties))
                    new_property.save()
            
            return HttpResponse(_(u"Features updated"))
                    
    elif request.method  == "DELETE":

        """
        Get the array with the feature ids for delete
        """
        feature_ids = json.loads(request.GET.get("ids","[]"))
        
        if len(feature_ids) == 0:
            return HttpResponseNotFound(_(u"You have to provide id of features to delete."))

        feature_queryset = Feature.objects.filter(id__in = feature_ids,
                                                user__exact = request.user)

            
        #set as expired
        exp_time = datetime.datetime.today()
        deleted_features = []
        for feat in feature_queryset:
            if(feat.expire_time == None):
                feat.expire_time = exp_time
                feat.save()
                deleted_features.append(feat.id)
                
        """
        Test if there were features already deleted (with an expiration time already set)
        and return not found
        """
        not_deleted = [id for id in feature_ids if id not in deleted_features]
        if len(not_deleted) > 0:
            return HttpResponseNotFound(_(u"Features %s not found and featured %s deleted." % (not_deleted, deleted_features)))
        
    
        return HttpResponse(_(u"Features with ids %s deleted." % deleted_features))
