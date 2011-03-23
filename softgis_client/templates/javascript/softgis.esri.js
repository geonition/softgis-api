/* global dojo, djConfig, console, esri  */



var api_full_url = "{{ method }}{{ host }}";

document.domain = "localhost:8000";

{% for client in softgis_clients %}
{{ client }}
{% endfor %}
