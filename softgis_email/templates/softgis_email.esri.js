

function get_email(callback_function)
{
    dojo.xhrGet({
        "url": api_full_url + "{% url api_manage_email %}",
        "handleAs": "json",
        "headers": {
            "Content-Type": "application/json",
            "X-CSRFToken": "{{ csrf_token }}"
            },
        "load": function(response, ioArgs) {
            if(callback_function !== undefined) {
                callback_function(response);
            }
            return response;
        },
        "error": function(response, ioArgs) {
            if (djconfig.debug) {
                console.error("HTTP status code: ", ioArgs.xhr.status);
            }
            return response;
        }
        });
}

function checkRegexp(o, regexp )
{
}

function validate_email(email_address)
{
}

function save_email(email_address, callback_function)
{
    dojo.xhrPost({
        "url": api_full_url + "{% url api_manage_email %}",
        "postData": encodeURIComponent(dojo.toJson(email_address)),
        "headers": {"Content-Type":"application/json",
                    "X-CSRFToken": "{{ csrf_token }}"},
        "failOk": true,
	    
        "handle": function(response, ioArgs) {
            if(callback_function !== undefined) {
                callback_function({"status_code": ioArgs.xhr.status,
                                  "message": ioArgs.xhr.responseText});
            }
        }
    });
}

function delete_email(callback)
{
    
}