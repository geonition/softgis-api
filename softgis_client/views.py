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
    the <app_name>.<lib>.js templates they provide.
    
    To get the right kind of javascript functions
    define a GET parameter:
    ?lib=esri --> returns the esri suitable javascript functions
    ?lib=jquery --> returns the jquery geojson functions
    """
    
    #default lib is esri
    lib = request.GET.get("lib", "esri")
    
    # get the templates
    softgis_templates = []
    for app in settings.INSTALLED_APPS:
        ind = app.find("softgis_")
        if ind != -1:
            softgis_templates.append(app[ind:] + "." + lib + ".js")
    
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
    return render_to_response("javascript/softgis."+ lib + ".js",
                              {'softgis_clients': softgis_clients},
                              mimetype="application/javascript")


def test_api(request):
    """
    This view function returns an HTML page that loads the
    dojo api and the softgis.js so that the API javascript
    functions can be tested from a javascript console.
    """
    
    #default lib is esri
    lib = request.GET.get("lib", "esri")
    
    return render_to_response("test/test.html",
                              {'lib' : lib},
                              context_instance = RequestContext(request))
    
    
def csrf(request):
    """
    This view returns a csrf token which can be used to send
    other POST requests to the REST api directly without using any
    Javascript library provided.
    """
 #this function gives recursion depth exeeded,, check it out later
 #   return HttpResponse(csrf(request)['csrf_token'],
  #                      mimetype="text/plain")
   
    return render_to_response("csrf.txt",
                              context_instance = RequestContext(request),
                              mimetype="text/plain")