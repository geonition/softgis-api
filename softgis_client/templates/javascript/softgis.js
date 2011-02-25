/* global dojo, djConfig, console, esri  */

dojo.require("dojo.cookie");



{% for client in softgis_clients %}
{{ client }}
{% endfor %}
