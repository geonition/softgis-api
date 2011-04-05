from django.http import HttpResponse
from django.contrib.sites.models import Site

class HttpResponseNotAuthorized(HttpResponse):
    status_code = 401

    def __init__(self):
        HttpResponse.__init__(self, "")
        #self['WWW-Authenticate'] = 'Basic realm="%s"' % Site.objects.get_current().name

