# Create your views here.
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.utils import translation

from softgis_profile.models import ProfileValue
from softgis_profile.models import StaticProfileValue
from softgis_profile.models import get_profiles

import settings

import sys

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json

# set the ugettext _ shortcut
_ = translation.ugettext
    
def profile(request):
    """
    This method handles the profile part of the
    REST api.
    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden(_("The request has to be made by an signed in user"))
        
    if(request.method == "GET"):
        # get the definied limiting parameters
        limiting_param = request.GET.items()

        profile_queryset = None
        
        #filter according to permissions
        if(request.user.has_perm('can_view_profiles')):
            profile_queryset = ProfileValue.objects.all()
        else:
            profile_queryset = \
                    ProfileValue.objects.filter(user__exact = request.user)

        profile_list = get_profiles(limiting_param, profile_queryset)
        
        return HttpResponse(json.dumps(profile_list))
    
    elif(request.method == "POST"):
        #mime type should be application/json    
        values = None
        
        try:
            values = json.loads(request.POST.keys()[0])
        except ValueError, err:
            return HttpResponseBadRequest("JSON error: " + str(err.args))

        allow_notifications = values.pop('allow_notifications', False)
        birthyear = values.pop('birthyear', None)
        gender = values.pop('gender', u'')
        email = values.pop('email', None)
        
        static_profile_values = \
                StaticProfileValue.objects.filter(user__exact = request.user)
        
        if len(static_profile_values) == 0:
            static_profile_values = \
                                StaticProfileValue(user_id = request.user.id)
        else:
            static_profile_values = static_profile_values[0]
            
        static_profile_values.allow_notifications = allow_notifications
        static_profile_values.birthyear = birthyear
        static_profile_values.gender = gender
        static_profile_values.email = email

        try:
            static_profile_values.full_clean()
        except ValidationError, err:
            return HttpResponseBadRequest(json.dumps(err.message_dict))

        static_profile_values.save()
        
        #confirm email TODO should use own version of confirmation
        if not email == "" and not email == None:
            email_addr = EmailAddress.objects.add_email(request.user, email)
            print "here"
            if email_addr == None:
                print "none"
                #django.db.connection.close()
                
        new_profile_value = ProfileValue(user = request.user,
                                        json_string = json.dumps(values))
        new_profile_value.save()
        
    return HttpResponse("")