# Create your views here.


       
#Views for the geometry API
def feature(request):
    """
    This function handles the feature part of the softgis REST api
    
    On GET request this function returns a geojson featurecollection
    matching the query string.
    
    On POST request this functions adds a new feature or modifies 
    the existing feature in the database.
    
    On DELETE request this function removes existing feature from 
    the database.
    
    Returns:
        200 if successful and geojson featurecollection (GET, POST)
        403 if not signed in
        400 if bad request

    """
    
    if request.method  == "GET":
        # get the definied limiting parameters
        limiting_param = request.GET.items()
        
        feature_collection = {"type":"FeatureCollection", "features": []}
        
        if not request.user.is_authenticated():
            return HttpResponseForbidden("")

        feature_queryset = None

        #filter according to permissions
        if(request.user.has_perm('softgis_api.can_view_all')):
            feature_queryset = Feature.objects.all()

        elif(request.user.has_perm('softgis_api.can_view_non_confidential')):
            #this has to be made better at some point
            feature_queryset = Feature.objects.exclude(category__exact = 'home')
        else:
            #else the user can only view his/her own features
            feature_queryset = \
                    Feature.objects.filter(user__exact = request.user)

        # transform geometries to the correct SpatialReferenceSystem
        #feature_queryset.transform(3067)

        #filter according to limiting_params
        property_queryset = Property.objects.all()

        for key, value in limiting_param:
            if(key == "user_id"):
                feature_queryset = \
                                feature_queryset.filter(user__exact = value)

            elif(key == "category"):
                feature_queryset = \
                                feature_queryset.filter(category__exact = value)
            else:
                property_queryset = property_queryset.filter(value_name = key,
                                                            value = value)

        
        #filter the features with wrong properties
        feature_id_list = property_queryset.values_list('feature_id', flat=True)

        # Not in use and gives database error in sqlite3
        # feature_queryset =
        #       feature_queryset.filter(id__in = list(feature_id_list))
        
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
        
        return HttpResponse(json.dumps(feature_collection))
        
            
    elif request.method  == "DELETE":
        
        feature_id = request.GET['id']
        
        feature_queryset = Feature.objects.filter(
                                                id__exact = feature_id,
                                                user__exact = request.user)

        if feature_queryset:
            feature_queryset.delete()
            return HttpResponse("")
        else:
            return HttpResponseBadRequest()
        
        
    elif request.method == "POST":
            
        feature_json = None
        
        feature_json = json.loads(request.POST.keys()[0])
        try:
            feature_json = json.loads(request.POST.keys()[0])
        except ValueError:
            return HttpResponseBadRequest(
                        "mime type should be application/json")

        
        identifier = None
        geometry = []
        properties = None
        category = None
        
        try:
            geometry = feature_json['geometry']
            properties = feature_json['properties']
            category = feature_json['properties']['category']
        except KeyError:
            return HttpResponseBadRequest("json requires properties"  + \
                                            "and geometry, and the" + \
                                            "properties a category value")
          
        try:
            identifier = feature_json['id']
        except KeyError:
            pass
            
        if identifier == None:
            #save a new feature if id is None
            
            #geos = GEOSGeometry(json.dumps(geometry))
            # Have to make OGRGeometry as GEOSGeometry
            # does not support spatial reference systems
            geos = OGRGeometry(json.dumps(geometry)).geos
            new_feature = None
            new_feature = Feature(geometry=geos,
                                    user=request.user,
                                    category=category)
            new_feature.save()

            #add the id to the feature json
            identifier = new_feature.id
            feature_json['id'] = identifier

            #save the properties of the new feature
            new_property = None
            new_property = Property(feature=new_feature,
                                    json_string=json.dumps(properties))
            new_property.save()
            
        else:
            #update old feature if id is given
            #only the feature properties is updated otherwise a
            #completely new feature should be added
            try:
                new_feature = Feature.objects.get(id__exact = identifier)
                new_property = Property(feature = new_feature,
                                        json_string = json.dumps(properties))
                new_property.save()
                
            except ObjectDoesNotExist:
                return HttpResponseBadRequest(
                            "no feature with the given id found")

        return HttpResponse(json.dumps(feature_json))
