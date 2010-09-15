{% load i18n %}
{% load cache %}

/* global dojo, djConfig, console, esri  */

/* login, logout, register, changepassword */

function register(username, password, email, notifications) {
    {% if not user.is_authenticated %}
    
    dojo.xhrPost({
	    "url": '{% url api_register %}', 
	    "handleAs": "json",
	    "postData": encodeURIComponent(dojo.toJson({
	        'username': username, 
	        'password': password,
	        'email': email,
	        'notifications': notifications
            })),
        "failOk": true,
	    "sync": false,
		"headers": {"Content-Type":"application/json"},
	    
	    // The LOAD function will be called on a successful response.
	    "load": function(response, ioArgs) {
	                window.location.reload();
			        return true;
		        },

	    // The ERROR function will be called in an error case.
	    "error": function(response, ioArgs) {
	                if(response.status === 409) {
	                    alert("{% trans 'Käyttäjätunnus on jo käytössä' %}");
	                } 
	                if (djConfig.debug) {
	                    console.error("HTTP status code: ", ioArgs.xhr.status);
                    }
                    return false;
                }
        });
    {% endif %}
}

function login(username, password) {    

    {% if not user.is_authenticated %}
    
    dojo.xhrPost({
	    "url": '{% url api_login %}', 
	    "handleAs": "json",
	    "postData": encodeURIComponent(dojo.toJson({
	        'username': username, 
	        'password': password
            })),
	    "sync": false,
		"headers": {"Content-Type":"application/json"},
	    
	    // The LOAD function will be called on a successful response.
	    "load": function(response, ioArgs) {
	                window.location.reload();
			        return true;
		        },

	    // The ERROR function will be called in an error case.
	    "error": function(response, ioArgs) {
	                if (djConfig.debug) {
	                    console.error("HTTP status code: ", ioArgs.xhr.status);
                    }
                    alert("{% trans 'Käyttäjätunnus ja salasana eivät täsmää' %}");
                    return false;
                }
        });
    {% endif %}
    
}

function logout() {

    {% if user.is_authenticated %}
    dojo.xhrGet({
	    "url": '{% url api_logout %}',
	    "sync": false,
	    
	    // The LOAD function will be called on a successful response.
	    "load": function(response, ioArgs) {
	                window.location.reload();
			        return true;
		        },

	    // The ERROR function will be called in an error case.
	    "error": function(response, ioArgs) {
	                if (djConfig.debug) {
	                    console.error("HTTP status code: ", ioArgs.xhr.status);
                    }
                    return false;
                }
        });
    {% endif %}
}

function new_password(username, email) {

    {% if not user.is_authenticated %}
    
    dojo.xhrPost({
	    "url": '{% url api_new_password %}', 
	    "handleAs": "json",
	    "postData": encodeURIComponent(dojo.toJson({
	        'username': username,
	        'email': email
            })),
	    "sync": false,
		"headers": {"Content-Type":"application/json"},
	    
	    // The LOAD function will be called on a successful response.
	    "load": function(response, ioArgs) {
			        return true;
		        },

	    // The ERROR function will be called in an error case.
	    "error": function(response, ioArgs) {
	                if (djConfig.debug) {
	                    console.error("HTTP status code: ", ioArgs.xhr.status);
                    }
                    return false;
                }
        });
    {% endif %} 
} 

function change_password(new_password) { 

    {% if user.is_authenticated %}
    
    dojo.xhrPost({
	    "url": '{% url api_change_password %}', 
	    "handleAs": "json",
	    "postData": encodeURIComponent(dojo.toJson({
	        'new_password': new_password
            })),
	    "sync": false,
		"headers": {"Content-Type":"application/json"},
	    
	    // The LOAD function will be called on a successful response.
	    "load": function(response, ioArgs) {
                    alert("{% trans 'Salasanasi on vaihdettu' %}");
			        return true;
		        },

	    // The ERROR function will be called in an error case.
	    "error": function(response, ioArgs) {
	                if (djConfig.debug) {
	                    console.error("HTTP status code: ", ioArgs.xhr.status);
                    }
                    return false;
                }
        });
    {% endif %}
        
}

/* PROFILE API begins */

/*
This function saves the profile value pairs given
*/
function save_profile_values(profile_value_pairs) {
    {% if user.is_authenticated %}
    
    var params = "?user_id={{ user.id }}"
    profile_value_pairs['user_id'] = {{ user.id }};
    
	dojo.xhrPost({
		"url": "{% url api_profile %}" + params,
		"handleAs": "json",
		"postData": encodeURIComponent(dojo.toJson(profile_value_pairs)),
	    "headers": {"Content-Type":"application/json"},
		"load": function(response, ioArgs) {
		            return;
				},
		"error": function(response,ioArgs) {
		            console.log(response);
			    }
    	});
    
    {% endif %}
}


/*
This variable is used to chache the profiles already queried
*/
var profile_values = {};

/*
This function returns an array of profiles.
*/

function get_profiles(limiter_param, callback_function) {

    {% if user.is_authenticated %}
    
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
        callback_function(profile_values[limiter_param]);
    }

    {% else %}

    return [];

    {% endif %}
}

/* PROFILE API ends */


/* FEATURE API begins*/


function save_graphic(graphic) {
    {% if user.is_authenticated %}
    
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
    
    {% endif %}
}

function remove_graphic(feature_id) {
    {% if user.is_authenticated %}
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
    {% endif %}
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
    {% if user.is_authenticated %}

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

                    for(var i = 0; i < response.features.length; i++) {
                        var geometry = response.features[i].geometry;
                        var properties = response.features[i].properties;
                        var id = response.features[i].id;
                        var graphic = new esri.Graphic({});

                        //graphicID and id should be the same
                        //properties.graphicID = id;

                        if(geometry.type === "Point") {
                            graphic.setGeometry(new esri.geometry.Point(geometry.coordinates));
                        } else if (geometry.type === "LineString") {
                            graphic.setGeometry(new esri.geometry.Polyline({"paths": [geometry.coordinates]}));
                        } else if(geometry.type === "Polygon") {
                            graphic.setGeometry(new esri.geometry.Polygon({"rings": geometry.coordinates}));
                        }
                        graphic.setAttributes(properties);
                        
                        graphic["id"] = id;
                        
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
    {% endif %}
}

/* FEATURE API ends */
