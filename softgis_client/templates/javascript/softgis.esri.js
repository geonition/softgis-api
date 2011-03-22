/* global dojo, djConfig, console, esri  */



var api_full_url = "{{ method }}{{ host }}";


{% for client in softgis_clients %}
{{ client }}
{% endfor %}
