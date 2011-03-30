/* global dojo, djConfig, console, esri  */
{% extends "javascript/softgis_client.commons.js" %}

{% block content %}
	{% for client in softgis_clients %}
	{{ client }}
	{% endfor %}
{% endblock %}
