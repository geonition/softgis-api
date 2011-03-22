
/*
This function saves the graphic given in GeoJSON format.

It takes as parameters:
graphic - a graphic in ESRI JSON notation
 
*/

function save_graphic(graphic) {
    
    var properties = graphic.attributes;
    
    //transform to geojson format
    var geojson_feature = {};
    geojson_feature.type = "Feature";
    geojson_feature.properties = properties;
    geojson_feature.geometry = {};
    
    if(graphic.geometry.type === "polyline") {
        geojson_feature.geometry.type = "LineString";
        geojson_feature.geometry.coordinates = graphic.geometry.paths[0];
    } else if(graphic.geometry.type === "point") {
        geojson_feature.geometry.type = "Point";
        geojson_feature.geometry.coordinates = [graphic.geometry.x,
                                                graphic.geometry.y];
    } else if(graphic.geometry.type === "polygon") {
        geojson_feature.geometry.type = "Polygon";
        geojson_feature.geometry.coordinates = graphic.geometry.rings;
    }
    
    if(graphic.id !== undefined && graphic.id !== null) {
        geojson_feature.id = graphic.id;
    }

    // add crs to the geometry
    geojson_feature.geometry.crs = {"type": "EPSG",
                                    "properties": {"code": graphic.geometry.spatialReference.wkid}};

    //add the parameters from the properties
    var params = "?category=" + geojson_feature.properties.category;
    if(geojson_feature.id !== undefined &&
        geojson_feature.id !== null) {
        
        params += "&id=" + geojson_feature.id;
    }
    
    dojo.xhrPost({
        "url": "{% url api_feature %}" + params,
        "handleAs": "json",
        "postData": encodeURIComponent(dojo.toJson(geojson_feature)),
        "headers": {"Content-Type":"application/json"},
        "load": function(response, ioArgs) {
                    if(djConfig.isDebug) {
                        console.log(ioArgs);
                        console.log(response);
                        console.log(response.id);
                    }
                    graphic.id = response.id;
                    graphic.attributes.graphicId = response.id;
		            
                    return graphic;
                },
        "error": function(response,ioArgs) {
                        console.log(response);
                }
        });
    
}

/*
This function removes a graphic.

It takes as parameters:
feature_id - id of the feature to be removed.
 
*/
function remove_graphic(feature_id) {
    dojo.xhrDelete({
		"url": '{% url api_feature %}?id=' + feature_id,
		"handleAs": "text",
                "headers": {"Content-Type":"application/json"},
		"failOk": true,
		"load": function(response, ioArgs) {
					if(djConfig.isDebug) {
						console.log(ioArgs);
						console.log(response);
						console.log(response.id);
					}
				},
		"error": function(response,ioArgs) {
		            console.log(response);
			}
	});
}

/*
Semaphore set with the layer as key

The problem is that there should only be one GET request
for each layer otherwise it adds the graphics twice.
*/
var LAYER_ADD_SEMAPHORES = {};

/*
The graphics queried from the server will be cached in the layer
but this helper variable tells if the layer graphics has already
been queried.
*/
var QUERIED_PARAM = {};

/*
This function gets graphics from the server

and adds them to the map_layer given

expects the layer to have a renderer of its own

It takes as parameters:
limiter_param - query string to limit the returned graphics
map_layer - the map layer where the graphics are added
infotemplate - an ESRI infotemplate object for the graphic

*/
function get_graphics(limiter_param, map_layer, infotemplate) {

    if(limiter_param === undefined ||
        limiter_param === null) {
        limiter_param = '';
    }

    //do not query twice with the same parameters
    if(QUERIED_PARAM[limiter_param]) {
        return;
    } else {
        QUERIED_PARAM[limiter_param] = true;
    }
    
    dojo.xhrGet({
        "url": '{% url api_feature %}' + limiter_param,
        "handleAs": "json",
        "sync": false,
        "headers": {"Content-Type":"application/json"},

        // The LOAD function will be called on a successful response.
        "load": function(response, ioArgs) {
                    var return_graphics = [];

                    LAYER_ADD_SEMAPHORES[limiter_param] = true;

                    var spatialReference = new esri.SpatialReference({"wkid": response.crs.properties.code});
                    for(var i = 0; i < response.features.length; i++) {
                        var geometry = response.features[i].geometry;
                        var properties = response.features[i].properties;
                        var id = response.features[i].id;
                        var graphic = new esri.Graphic({});

                        //graphicID and id should be the same
                        //properties.graphicID = id;
                        if(geometry.type === "Point") {
                            graphic.setGeometry(new esri.geometry.Point(geometry.coordinates).setSpatialReference(spatialReference));
                        } else if (geometry.type === "LineString") {
                            graphic.setGeometry(new esri.geometry.Polyline({"paths": [geometry.coordinates]}).setSpatialReference(spatialReference));
                        } else if(geometry.type === "Polygon") {
                            graphic.setGeometry(new esri.geometry.Polygon({"rings": geometry.coordinates}).setSpatialReference(spatialReference));
                        }
                        graphic.setAttributes(properties);
                        
                        graphic.id = id;
                        
                        if(infotemplate !== undefined) {
                            graphic.setInfoTemplate(infotemplate);
                        }
                        
                        if(map_layer !== undefined) {
                            map_layer.add(graphic);
                        }
                        return_graphics.push(graphic);
                        
                    }
                    
                    LAYER_ADD_SEMAPHORES[limiter_param] = false;
                    
                    return return_graphics;
                },

        // The ERROR function will be called in an error case.
        "error": function(response, ioArgs) {
            if (djConfig.debug) {
                console.error("HTTP status code: ", ioArgs.xhr.status);
            }
            return response;
        }
    });
}