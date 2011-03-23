# Create your views here.
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.utils import translation
from softgis_profile.models import Profile
from django.core.exceptions import ObjectDoesNotExist

import settings
import datetime
import sys

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json

# set the ugettext _ shortcut
_ = translation.ugettext

USE_MONGODB = getattr(settings, "USE_MONGODB", False)

def profile(request):
    """
    This method handles the profile part of the
    REST api.
    """
    def parse_time(time_string):
        """
        Helper function to parse a POST or GET time
        from the following format:
        yyyy-mm-dd-HH-MM-SS
        
        yyyy - year
        mm - month
        dd - day
        HH - hour
        MM - minute
        SS - second
        
        The less accurate time value have to be given before any less
        accurate time value.
        
        returns a datetime.datetime instance
        """
        time_accuracy = time_string.count('-')
        if time_accuracy == 0:
            return datetime.datetime.strptime(time_string, "%Y")
        elif time_accuracy == 1:
            return datetime.datetime.strptime(time_string, "%Y-%m")
        elif time_accuracy == 2:
            return datetime.datetime.strptime(time_string, "%Y-%m-%d")
        elif time_accuracy == 3:
            return datetime.datetime.strptime(time_string, "%Y-%m-%d-%H")
        elif time_accuracy == 4:
            return datetime.datetime.strptime(time_string, "%Y-%m-%d-%H-%M")
        elif time_accuracy == 5:
            return datetime.datetime.strptime(time_string, "%Y-%m-%d-%H-%M-%S")
            
            
    if not request.user.is_authenticated():
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
            if key == 'user_id':
                profile_queryset = profile_queryset.filter(user_id__exact = value)
                
            elif key == 'time':
                dt = parse_time(value)
                profile_qs_expired = profile_queryset.filter(create_time__lte = dt)
                profile_qs_expired = profile_qs_expired.filter(expire_time__gte = dt)
                profile_qs_not_exp = profile_queryset.filter(create_time__lte = dt)
                profile_qs_not_exp = profile_qs_not_exp.filter(expire_time = None)
                profile_queryset = profile_qs_not_exp | profile_qs_expired
                
            elif USE_MONGODB:
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

                elif command == "":
                    mongo_query[key] = value
        
        #filter the queries acccording to the json
        if len(mongo_query) > 0:
            qs = Profile.mongodb.find(mongo_query)
            profile_queryset = profile_queryset.filter(id__in = qs.values_list('id', flat=True))
            
            
        profile_list = []
        for prof in profile_queryset:
            profile_list.append(prof.json())
        
        return HttpResponse(json.dumps(profile_list))
    
    elif(request.method == "POST"):
        #mime type should be application/json    
        values = None
        
        try:
            values = json.loads(request.POST.keys()[0])
        except ValueError, err:
            return HttpResponseBadRequest("JSON error: " + str(err.args))

        current_profile = None
        try:
            current_profile = Profile.objects.latest('create_time')
            
            current_profile.update(json.dumps(values))
            
        except ObjectDoesNotExist:
            
            new_profile_value = Profile(user = request.user,
                                       json_string = json.dumps(values))
            new_profile_value.save()
            
        
        return HttpResponse(_("The profile has been saved"))
        
    return HttpResponseBadRequest(_("This function only support GET and POST methods"))