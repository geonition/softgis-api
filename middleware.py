

class CrossSiteAccessMiddleware(object):
    """
    This middleware adds cross site acces headers
    to the reponse.
    """
    
    def _set_access_headers(response):
        
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, GET, DELETE, PUT, OPTIONS'
        response['Access-Control-Max-Age'] = 1000
        response['Access-Control-Allow-Headers'] = '*'
        
    
    def process_request(self, request):
        if request.method == "OPTIONS":
        
            self._set_access_headers(response)
        
            return HttpResponse()
            
        return None
    
    
    def process_response(self, request, response):
        
        self._set_access_headers(response)
        
        return response
    