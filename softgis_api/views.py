# -*- coding: utf-8 -*-
"""
This file includes all the views for the api
"""
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotFound
from django.template import loader
from django.template import RequestContext
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth import authenticate as django_authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from softgis_api.models import ProfileValue
from softgis_api.models import Feature
from softgis_api.models import Property
from softgis_api.models import get_profiles
from emailconfirmation.models import EmailAddress
from django.core.mail import send_mail 
from django.core.mail import BadHeaderError
from django.contrib.gis.geos import GEOSGeometry
from random import Random
from django.utils import translation
from django.views.decorators.cache import cache_page
import values

import sys

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json

# set the ugettext _ shortcut
_ = translation.ugettext
   
def login(request):
    """
    This function does the login procedure and returns
    a suitable status code
    

    Returns 200 if successful
            400 for Bad Request
            401 for unauthorized (wrong password or username not found)

    """
    try:
    
    
        request_json = None
        try:
            request_json = eval(request.POST.keys()[0])
        except Exception:
            return HttpResponseBadRequest("mime type should be application/json")
         
        username = request_json['username']
        password = request_json['password']
     

        user = django_authenticate(username=username, password=password)
        

        
        if user is not None:
            django_login(request, user)
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=401)
    except TypeError:
        return HttpResponseBadRequest()
    except Exception:
        return HttpResponseBadRequest()

def logout(request):
    """
    simple logout function

    Returns
        200 if logout successful
        400 if an error occures (no one is logged in)
    """
    try:
        django_logout(request)
        return HttpResponse("")
    except:
        return HttpResponseBadRequest()

    
def register(request):
    """
    This function handles the registration form.

    GET
    does nothing at the moment, returns 200 OK

    POST
    With a POST request it registers a user if the values
    provided is correct

    The post should include
    {
    'username': <required>,
    'password': <required>.
    'email': <optional>,
    'notifications': <optional>
    }

    if email is provided it will be confirmed with an confirmation link
    sent to the user.

    notifications is if the user wants notification of updates to the service
    to his/her email
    
    
    Returns 201 if successful
            400 for Bad Request
            409 for Conflict

    """
    if(request.method == "GET"):    
        return HttpResponse("")

    elif(request.method == "POST"):

        if request.user.is_authenticated() == True:
            return HttpResponseBadRequest("You cannot register a user" + \
                                          "when logged in")
        
    
        request_json = None
        try:
            request_json = eval(request.POST.keys()[0])
        except Exception:
            return HttpResponseBadRequest("mime type should be application/json")
            
            
        try:
            username = request_json['username']
            password = request_json['password']
            try:
                email = request_json['email']
            except KeyError:
                email = ''
            try:
                notifications = request_json['notifications']
            except KeyError:
                notifications = ''
                
            #create user for django auth
            user = User.objects.create_user(username, \
                                            email, \
                                            password)
            user.save()


            user = django_authenticate(username=username, \
                                        password=password)
            if user is not None and user.is_active:
                django_login(request, user)
                
            if not email == '':
                email_addr = EmailAddress.objects.add_email(user, email)

            if notifications == 'yes':
                new_profile_value = ProfileValue(user=user,
                                                value_name="notifications",
                                                value=str(notifications))
                new_profile_value.save()
            
            return HttpResponse(status=201)
        
        except IntegrityError:
            return HttpResponse(status=409)
        except Exception:
            return HttpResponseBadRequest()

def new_password(request):
    """
    
    """
    
    if(request.method == "POST"):
    
        request_json = json.loads(request.POST.keys()[0])
        
        username = request_json['username']
        email = request_json['email']
        user = None
        
        if not username == None:
            try:
                user = User.objects.get(username__exact = username)
            except:
                pass
        
        if not email == None:
            try:
                user = User.objects.get(email__exact = email)
            except:
                pass
                
        if user == None:
            return HttpResponseNotFound("username or email does not match existing user")
        
        elif user.email == None:
            return HttpResponseBadRequest("user has no email")
            
        rnd = Random()
        
        righthand = '23456qwertasdfgzxcvbQWERTASDFGZXCVB'
        lefthand = '789yuiophjknmYUIPHJKLNM'
        allchars = righthand + lefthand
        
        passwordlength = 8
        
        password = ""
        
        for i in range(passwordlength):
            if i%2:
                password += rnd.choice(righthand)
            else:
                password += rnd.choice(lefthand)
        
        subject = _('Uusi salasana pehmogis sivustolle')
        message = user.username + _(' uusi salasana on: ') + password
        
        try:
            send_mail(subject, message, 'do_not_reply@pehmogis.fi', [user.email])
            user.set_password(password)
            user.save()
            return HttpResponse()
        except BadHeaderError:
            return HttpResponseBadRequest('Invalid header found.')
            

    return HttpResponseBadRequest("This URL only accepts POST requests")
    
def change_password(request):
    if(request.method == "POST"):
        
        request_json = json.loads(request.POST.keys()[0])
        
        new_password = request_json['new_password']
        
        request.user.set_password(new_password)
        request.user.save()
        
        return HttpResponse()
        
    return HttpResponseBadRequest()   
    
def profile(request):
    """
    This method handles the profile part of the
    REST api.
    """
    
    if(request.method == "GET"):
        # get the definied limiting parameters
        limiting_param = request.GET.items()
        
        if not request.user.is_authenticated():
            return HttpResponseForbidden();

        profile_queryset = None
        
        #filter according to permissions
        if(request.user.has_perm('can_view_profiles')):
            profile_queryset = ProfileValue.objects.all()
        else:
            profile_queryset = ProfileValue.objects.filter(user__exact = request.user)

        profile_list = get_profiles(limiting_param, profile_queryset)
        
        return HttpResponse(json.dumps(profile_list))
    
    elif(request.method == "POST"):
        #mime type should be application/json    
        values = None
        
        try:
            values = json.loads(request.POST.keys()[0])
        except Exception:
            return HttpResponseBadRequest("mime type should be application/json")

        try:
            email = values['email']
            email_addr = EmailAddress.objects.add_email(request.user, email)
        except KeyError:
            pass

        new_profile_value = ProfileValue(user = request.user,
                                        json_string = request.POST.keys()[0])

        new_profile_value.save()
        
        
    return HttpResponse("")
        
#Views for the geometry API
def feature(request):
    
    
    if request.method  == "GET":
        # get the definied limiting parameters
        limiting_param = request.GET.items()
        
        feature_collection = {"type":"FeatureCollection", "features": []}
        
        if not request.user.is_authenticated():
            return HttpResponseForbidden("")

        feature_queryset = None

        #filter according to permissions
        if(request.user.has_perm('softgis_api.can_view_all')):
            feature_queryset = Feature.objects.all()

        elif(request.user.has_perm('softgis_api.can_view_non_confidential')):
            #this has to be made better at some point
            feature_queryset = Feature.objects.exclude(category__exact = 'home')
        else:
            #else the user can only view his/her own features
            feature_queryset = Feature.objects.filter(user__exact = request.user)

        #filter according to limiting_params
        property_queryset = Property.objects.all()

        for key, value in limiting_param:
            if(key == "user_id"):
                feature_queryset = \
                                feature_queryset.filter(user__exact = value)

            elif(key == "category"):
                feature_queryset = \
                                feature_queryset.filter(category__exact = value)
            else:
                property_queryset = property_queryset.filter(value_name = key, value = value)

        
        #filter the features with wrong properties
        feature_id_list = property_queryset.values_list('feature_id', flat=True)

        # Not in use and gives database error in sqlite3
        #feature_queryset = feature_queryset.filter(id__in = list(feature_id_list))
        
        for feature in feature_queryset:
            feature_collection['features'].append(feature.geojson())

        return HttpResponse(json.dumps(feature_collection))
        
            
    elif request.method  == "DELETE":
        
        feature_id = request.GET['id']
        
        feature_queryset = Feature.objects.filter(
                                                id__exact = feature_id,
                                                user__exact = request.user)

        if feature_queryset:
            feature_queryset.delete()
            return HttpResponse("")
        else:
            return HttpResponseBadRequest()
        
        
    elif request.method == "POST":
    
        feature_json = None
        
        try:
            feature_json = json.loads(request.POST.keys()[0])
        except Exception:
            return HttpResponseBadRequest("mime type should be application/json")

        
        identifier = None
        geometry = []
        properties = None
        category = None
        
        try:
            geometry = feature_json['geometry']
            properties = feature_json['properties']
            category = feature_json['properties']['category']
        except KeyError:
            return HttpResponseBadRequest("json requires properties and geometry, \
                                            and the properties a category value")
          
        try:
            identifier = feature_json['id']
        except KeyError:
            pass
            
        if identifier == None:
            #save a new feature if id is None
            
            geos = GEOSGeometry(json.dumps(geometry))
            
            new_feature = None
            new_feature = Feature(geometry=geos, user=request.user, category=category)
            new_feature.save()

            #add the id to the feature json
            identifier = new_feature.id
            feature_json['id'] = identifier

            #save the properties of the new feature
            new_property = None
            new_property = Property(feature=new_feature,
                                    json_string=json.dumps(properties))
            new_property.save()
            
        else:
            #update old feature if id is given
            #only the feature properties is updated otherwise a completely new feature should be added
            try:
                new_feature = Feature.objects.get(id__exact = identifier)
                new_property = Property(feature = new_feature, json_string = json.dumps(properties))
                new_property.save()
                
            except ObjectDoesNotExist:
                return HttpResponseBadRequest("no feature with the given id found")

        return HttpResponse(json.dumps(feature_json))


def javascript_api(request):
    context_dict = {}
    
    template = loader.get_template('javascript/softgis.js')
    context = RequestContext(request, context_dict)

    return HttpResponse(template.render(context), mimetype="application/javascript")
