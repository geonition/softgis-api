# Create your views here.
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.utils import translation
from softgis_profile.models import Profile
from django.core.exceptions import ObjectDoesNotExist
from Commons import SoftGISFormatUtils

import settings
import logging
import sys
import datetime

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json

# set the ugettext _ shortcut
_ = translation.ugettext
logger = logging.getLogger('api.profile.view')

USE_MONGODB = getattr(settings, "USE_MONGODB", False)

def profile(request):
    """
    This method handles the profile part of the
    REST api.
    """
   
            
    if not request.user.is_authenticated():
        logger.warning("A %s request was received in the profile but the user is not authenticated" % request.method)
        return HttpResponseForbidden(_("The request has to be made by an signed in user"))
        
    if(request.method == "GET"):
        # get the definied limiting parameters
        limiting_param = request.GET.items()

        profile_queryset = None
        
        #filter according to permissions
        if(request.user.has_perm('can_view_profiles')):
            profile_queryset = Profile.objects.all()
        else:
            profile_queryset = \
                    Profile.objects.filter(user__exact = request.user)
        
        mongo_query = {}

        #set up the query
        for key, value in limiting_param:
            
            key = str(key)
            if value.isnumeric():
                value = int(value)
            elif value == "true":
                value = True
            elif value == "false":
                value = False
                
            key_split = key.split('__')
            command = ""
            if len(key_split) > 1:
                command = key_split[1]
                key = key_split[0]
                    
            if key == 'user_id':
                profile_queryset = profile_queryset.filter(user__exact = value)
                
            elif key == 'time':
                
                dt = None
                
                if command == 'now' and value:
                    dt = datetime.datetime.now()
                elif command == 'now' and not value:
                    continue
                else:
                    dt = SoftGISFormatUtils.parse_time(value)
                
                profile_qs_expired = profile_queryset.filter(create_time__lte = dt)
                profile_qs_expired = profile_qs_expired.filter(expire_time__gte = dt)
                profile_qs_not_exp = profile_queryset.filter(create_time__lte = dt)
                profile_qs_not_exp = profile_qs_not_exp.filter(expire_time = None)
                profile_queryset = profile_qs_not_exp | profile_qs_expired
                
            elif USE_MONGODB:
                
                if command == "max":

                    if mongo_query.has_key(key):
                        mongo_query[key]["$lte"] = value
                    else:
                        mongo_query[key] = {}
                        mongo_query[key]["$lte"] = value
                        
                elif command == "min":

                    if mongo_query.has_key(key):
                        mongo_query[key]["$gte"] = value
                    else:
                        mongo_query[key] = {}
                        mongo_query[key]["$gte"] = value
                        
                elif command == "range":
                    value_l = value.split('-')
                    if mongo_query.has_key(key):
                        mongo_query[key]["$gte"] = int(value_l[0])
                        mongo_query[key]["$lte"] = int(value_l[1])
                    else:
                        mongo_query[key] = {}
                        mongo_query[key]["$gte"] = int(value_l[0])
                        mongo_query[key]["$lte"] = int(value_l[1])
                        
                elif command == "":
                    mongo_query[key] = value
        
        
        #filter the queries acccording to the json
        if len(mongo_query) > 0:
            qs = Profile.mongodb.find(mongo_query)
            profile_queryset = profile_queryset.filter(id__in = qs.values_list('id', flat=True))
            
        
        
        profile_list = []
        for prof in profile_queryset:
            profile_list.append(prof.json())

        logger.info("The GET request for user %s with the params %s returned successfully %s" %(request.user.username, limiting_param, profile_list))

        return HttpResponse(json.dumps(profile_list),  mimetype="application/json")
    
    elif(request.method == "POST"):
        #mime type should be application/json    
        values = None
        
        try:
            values = json.loads(request.POST.keys()[0])
        except ValueError, err:
            logger.warning("The json received via POST to profile was not valid: %s" %request.POST.keys()[0])
            return HttpResponseBadRequest("JSON error: " + str(err.args))
        except IndexError:
            return HttpResponseBadRequest(_("POST data was empty so could not save the profile"))

        current_profile = None
        try:
            current_profile = Profile.objects.filter(user__exact = request.user).latest('create_time')
            
            current_profile.update(json.dumps(values))
            
            
        except ObjectDoesNotExist:
            logger.info("The user %s does not have a profile" % request.user.username)

            new_profile_value = Profile(user = request.user,
                                       json_string = json.dumps(values))
            new_profile_value.save()

            logger.info("The profile %s for user %s was saved successfully" % (values, request.user.username))

        return HttpResponse(_("The profile has been saved"))
        
    return HttpResponseBadRequest(_("This function only support GET and POST methods"))