
{% extends "javascript/softgis_client.commons.js" %}

 
{% block library_specific_block %}

    //valid for jquery 6.1
    function add_CSRF_token_in_request_header()
    {
        $.ajaxPrefilter(function (options, originalOptions, jqXHR) {
                var CSRFverificationToken = getCookie( CSRF_Cookie_Name );
                if (CSRFverificationToken) {
                    jqXHR.setRequestHeader("X-CSRFToken", CSRFverificationToken);
                }
        });
    }

	{% for client in softgis_clients %}
	{{ client }}
	{% endfor %}

{% endblock %}
