/* global dojo, djConfig, console, esri  */

dojo.require("dojo.cookie");

{% csrf_token %}

{% for client in softgis_clients %}
{{ client }}
{% endfor %}
