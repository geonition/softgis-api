

/*
This function saves the profile value pairs given

It takes as parameters:
profile_value_pairs - JSON object containing new profile values
callback_function - a callback function that will be called when a reponse
                    from the server is received (optional)
**/
function save_profile_values(profile_value_pairs, callback_function) {
    dojo.xhrPost({
        "url": api_full_url + "{% url api_profile %}",
        "handleAs": "json",
        "postData": encodeURIComponent(dojo.toJson(profile_value_pairs)),
        "headers": {"Content-Type":"application/json",
                    "X-CSRFToken": getCookie( CSRF_Cookie_Name )},
        "failOk": true,
	    
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

It takes as parameters:
limiter_param - query string to limit the returned profiles e.g. "?latest=true&age=12"
callback_function - a callback function that will be called when a reponse
                    from the server is received (optional)
*/
function get_profiles(limiter_param, callback_function) {

    
    if(limiter_param === undefined ||
        limiter_param === null) {
        limiter_param = '';
    }
    
    if(profile_values[limiter_param] === undefined) {

        dojo.xhrGet({
            "url": api_full_url + '{% url api_profile %}' + limiter_param,
            "handleAs": "json",
            "failOk": true,
            "headers": {"Content-Type":"application/json",
                    "X-CSRFToken": getCookie( CSRF_Cookie_Name )},

            // The LOAD function will be called on a successful response.
            "load": function(response, ioArgs) {
                        if(callback_function !== undefined) {
                            callback_function(response, ioArgs);
                        }
                        profile_values[limiter_param] = response;
                        return response;
                    },

            // The ERROR function will be called in an error case.
            "error": function(response, ioArgs) {
                        if(callback_function !== undefined) {
                            callback_function(response, ioArgs);
                        }
                        if (djConfig.debug) {
                            console.error("HTTP status code: ", ioArgs.xhr.status);
                        }
                        return response;
                    }
            });
            
    } else if(callback_function !== undefined) {
            callback_function(profile_values[limiter_param]);
    }
   

    return [];

}
