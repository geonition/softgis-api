

class CrossSiteAccessMiddleware(object):
    """
    This middleware adds cross site acces headers
    to the reponse.
    """
    
    def process_response(self, request, response):
        
        if request.method == "OPTIONS":
            response = HttpResponse()
        
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, GET, DELETE, PUT, OPTIONS'
        response['Access-Control-Max-Age'] = 1000
        response['Access-Control-Allow-Headers'] = '*'
        
        return response
    