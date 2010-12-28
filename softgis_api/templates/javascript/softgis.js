/* global dojo, djConfig, console, esri  */

/*
 This function registers the a new user
 
 The function takes the following parameters:
 username - username of the user to be created (required)
 password - password for the user to be created (required)
 email - email of the user to be created (optional)
 allow_notifications - boolean if the user wants updates/news to the email (optional)
 callback_function - function to be called after the response is received (optional)
 
 The callback_function will be passed the following parameters in a JSON object:
 status_code = 201/400/409
 message = message from server
*/
function register(username, password, email, allow_notifications, callback_function) {
    var data = {};
    data['username'] = (username !== undefined) ? username : null;
    data['password'] = (password !== undefined) ? password : null;
    data['email'] = (email !== undefined) ? email : null;
    data['allow_notifications'] = (allow_notifications !== undefined) ? allow_notifications : false;
    
    dojo.xhrPost({
        "url": '{% url api_register %}', 
        "handleAs": "json",
        "postData": encodeURIComponent(dojo.toJson(data)),
        "failOk": true,
        "headers": {"Content-Type":"application/json"},
        
        "handle": function(response, ioArgs) {
            if(callback_function !== undefined) {
                callback_function({"status_code": ioArgs.xhr.status,
                                  "message": ioArgs.xhr.responseText});
            }
        }
    });
}

/*
 This function signs a user into the service.
 
 The function requires two parameters:
 username - The username of the user to sign in (required)
 password - The password of the user (required)
 callback_function - This function is called when the response is received from
                    the server. (optional)
                    
 The callback_function will be passed the following parameters in a JSON object:
 status_code = 201/400/409
 message = message from server
*/
function login(username, password, callback_function) {
    var data = {};
    data['username'] = (username !== undefined) ? username : null;
    data['password'] = (password !== undefined) ? password : null;
    
    dojo.xhrPost({
	    "url": '{% url api_login %}', 
	    "handleAs": "json",
	    "postData": encodeURIComponent(dojo.toJson(data)),
            "failOk": true,
	    "headers": {"Content-Type":"application/json"},
	    
            "handle": function(response, ioArgs) {
                if(callback_function !== undefined) {
                    callback_function({"status_code": ioArgs.xhr.status,
                                      "message": ioArgs.xhr.responseText});
                }
            }
        });
}

/*
 The logout function send a logout request to the server
 
 The server returns 200 if logout successfull and
 400 if an error occured (no one is logged in)
 
 The logout function takes as parameter a callback function
 which will be passed the following parameters:
 status_code = 200
 message = message from server
*/
function logout(callback_function) {
    dojo.xhrGet({
	"url": '{% url api_logout %}',
	    
        "handle": function(response, ioArgs) {
            if(callback_function !== undefined) {
                callback_function({"status_code": ioArgs.xhr.status,
                                  "message": ioArgs.xhr.responseText});
            }
        }
    });
}

/*
 This function send a new password for the user
 with the email or username provided.
 
 Takes as parameters:
 username - the username of the person who need a new password (required if email is not provided)
 email - email of the person that needs a new password (required if username is not provided)
 callback_function - the function to be called when a response from the server
                    is received (optional)
*/
function new_password(email, callback_function) {

    var data = {};
    data['email'] = (email !== undefined) ? email : null;
    
    dojo.xhrPost({
        "url": '{% url api_new_password %}', 
        "handleAs": "json",
        "postData": encodeURIComponent(dojo.toJson(data)),
        "sync": false,
        "headers": {"Content-Type":"application/json"},
	    
        "handle": function(response, ioArgs) {
            if(callback_function !== undefined) {
                callback_function({"status_code": ioArgs.xhr.status,
                                  "message": ioArgs.xhr.responseText});
            }
        }
    });
}

/*
 This function changes the password for a user.
 
 It takes as parameters:
 new_password - the new password to change the old one to (required)
 callback_function - a callback function that will be called when a reponse
                    from the server is received (optional)
*/
function change_password(new_password, callback_function) { 
    
    dojo.xhrPost({
	"url": '{% url api_change_password %}', 
	"handleAs": "json",
	"postData": encodeURIComponent(dojo.toJson({
            'new_password': new_password
        })),
	"sync": false,
	"headers": {"Content-Type":"application/json"},
	    
        "handle": function(response, ioArgs) {
            if(callback_function !== undefined) {
                callback_function({"status_code": ioArgs.xhr.status,
                                  "message": ioArgs.xhr.responseText});
            }
        }
    });
}

/* PROFILE API begins */

/*
This function saves the profile value pairs given
*/
function save_profile_values(profile_value_pairs, callback_function) {
    
    var params = "?user_id={{ user.id }}";
    profile_value_pairs.user_id = {{ user.id }};
    
    dojo.xhrPost({
        "url": "{% url api_profile %}" + params,
        "handleAs": "json",
        "postData": encodeURIComponent(dojo.toJson(profile_value_pairs)),
        "headers": {"Content-Type":"application/json"},
	    
        "handle": function(response, ioArgs) {
            if(callback_function !== undefined) {
                callback_function({"status_code": ioArgs.xhr.status,
                                  "message": ioArgs.xhr.responseText});
            }
        }
    });
}


/*
This variable is used to chache the profiles already queried
*/
var profile_values = {};

/*
This function returns an array of profiles.
*/

function get_profiles(limiter_param, callback_function) {

    
    if(limiter_param === undefined ||
        limiter_param === null) {
        limiter_param = '';
    }

    if(profile_values[limiter_param] === undefined) {

        dojo.xhrGet({
            "url": '{% url api_profile %}' + limiter_param,
            "handleAs": "json",
            "sync": false,
            "headers": {"Content-Type":"application/json"},

            // The LOAD function will be called on a successful response.
            "load": function(response, ioArgs) {
                        if(callback_function !== undefined) {
                            callback_function(response);
                        }
                        profile_values[limiter_param] = response;
                        return response;
                    },

            // The ERROR function will be called in an error case.
            "error": function(response, ioArgs) {
                        if (djConfig.debug) {
                            console.error("HTTP status code: ", ioArgs.xhr.status);
                        }
                        return response;
                    }
            });
            
    } else {
        if(callback_function !== undefined) {
            callback_function(profile_values[limiter_param]);
        }
    }

    return [];

}

/* PROFILE API ends */


/* FEATURE API begins*/


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

/* FEATURE API ends */
