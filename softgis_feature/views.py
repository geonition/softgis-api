from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.core.exceptions import ObjectDoesNotExist
from django.utils import translation
from django.utils.encoding import smart_unicode
import urllib2

from django.contrib.gis.gdal import OGRGeometry

from softgis_feature.models import Feature
from softgis_feature.models import Property


import settings

import sys

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json

_ = translation.ugettext


#Views for the geometry API
def feature(request):
    """
    This function handles the feature part of the softgis REST api
    
    On GET request this function returns a geojson featurecollection
    matching the query string.
    
    On POST request this function adds a new feature to the database.
    
    On PUT request this function will update a feature that has
    a given id.
    
    On DELETE request this function removes existing feature from 
    the database with the given id.
    
    Returns:
        200 if successful and geojson featurecollection (GET, POST)
        403 if not signed in
        400 if bad request

    """
    
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
        
        #filter according to limiting_params
        for key, value in limiting_param:
            if(key == "user_id"):
                feature_queryset.objects.filter(user__exact = value)
            elif(key == "time"):
                # value in the form 'yyyy-mm-dd' ?
                feature_queryset.objects.filter(create_time__lte = value)
                feature_queryset.objects.filter(expire_time__gte = value)
            else:
                property_queryset = property_queryset.filter(value_name = key,
                                                            value = value)

        
        #filter the features with wrong properties
        feature_id_list = property_queryset.values_list('feature_id', flat=True)

        # gives database error in sqlite3 ?
        feature_queryset = feature_queryset.filter(id__in = list(feature_id_list))
        
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
        geometry = None
        properties = None
        
        try:
            geometry = feature_json['geometry']
            properties = feature_json['properties']
        except KeyError:
            return HttpResponseBadRequest("geojson feature requires " + \
                                        "properties "  + \
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
        
    elif request.method == "PUT":
        
        #supports updating geojson Features
        feature_json = json.loads(urllib2.unquote(request.raw_post_data.encode('utf-8')).decode('utf-8'))
        geometry = None
        properties = None
        feature_id = None
        
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

    elif request.method  == "DELETE":
        
        feature_id = request.GET.get('id', -1)
        
        feature_queryset = Feature.objects.filter(id__exact = feature_id,
                                                user__exact = request.user)

        if len(feature_queryset) > 0:
            feature_queryset.delete()
            return HttpResponse(_(u"Feature with id %s deleted" % feature_id))
        else:
            return HttpResponseNotFound(_(u"Feature with given id was not found"))