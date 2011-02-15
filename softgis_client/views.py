from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse

def javascript_api(request):
    context_dict = {}
    
    template = loader.get_template('javascript/softgis.js')
    context = RequestContext(request, context_dict)

    return HttpResponse(template.render(context),
                        mimetype="application/javascript")


def test_api(request):
    """
    This view function returns an HTML page that loads the
    dojo api and the softgis.js so that the API javascript
    functions can be tested from a javascript console.
    """
    return render_to_response("test/test_dojo.html",
                              context_instance = RequestContext(request))