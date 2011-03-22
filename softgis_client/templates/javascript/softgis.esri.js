/* global dojo, djConfig, console, esri  */

var api_full_url = "{{ api_full_url }}";



{% for client in softgis_clients %}
{{ client }}
{% endfor %}
