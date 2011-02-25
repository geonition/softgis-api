from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.template import RequestContext
from django.template import TemplateDoesNotExist
from django.http import HttpResponse
import settings

def javascript_api(request):
    """
    This function returns the javascript client
    that was requested.
    
    The client will be a combination of the
    other installed softgis_* applications and
    the <app_name>.js templates they provide.
    """
    # get the templates
    softgis_templates = []
    for app in settings.INSTALLED_APPS:
        ind = app.find("softgis_")
        if ind != -1:
            softgis_templates.append(app[ind:] + ".js")
    
    # render the clients to strings
    softgis_clients = []
    for template in softgis_templates:
        try:
            softgis_clients.append(
                render_to_string(
                    template,
                    RequestContext(request)
                ))
        except TemplateDoesNotExist:
            pass
    
    # return the clients in one file
    return render_to_response("javascript/softgis.js",
                              {'softgis_clients': softgis_clients},
                              mimetype="application/javascript")


def test_api(request):
    """
    This view function returns an HTML page that loads the
    dojo api and the softgis.js so that the API javascript
    functions can be tested from a javascript console.
    """
    return render_to_response("test/test_dojo.html",
                              context_instance = RequestContext(request))
    
    
def csrf(request):
    """
    This view returns a csrf token which can be used to send
    other POST requests to the REST api directly without using any
    Javascript library provided.
    """
    return render_to_response("csrf.txt",
                              context_instance = RequestContext(request),
                              mimetype="text/plain")