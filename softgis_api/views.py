# -*- coding: utf-8 -*-
"""
This file includes all the views for the api
"""
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotFound
from django.http import HttpResponseRedirect
from django.template import loader
from django.template import RequestContext
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth import authenticate as django_authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
#from pehmogis.api.softgis_api.models import geometry
from softgis_api.models import ProfileValue
from softgis_api.models import Feature
from softgis_api.models import Property
from softgis_api.models import StaticProfileValue
from softgis_api.models import get_profiles
from emailconfirmation.models import EmailAddress
from django.core.mail import send_mail 
from django.core.mail import BadHeaderError
from random import Random
from django.utils import translation
from django.contrib.gis.gdal import OGRGeometry
from openid2rp.django import auth as openid_auth
from django.shortcuts import render_to_response


import django
import api_settings as settings
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
    

    Returns:
        200 if successful
        400 for Bad Request
        401 for unauthorized (wrong password or username not found)

    """
    if(request.method == "GET"):
        return HttpResponseBadRequest(_("This url only accept POST requests"))
        
    elif (request.method == "POST"):
        if request.user.is_authenticated() == True:
            return HttpResponseBadRequest(_("You have already signed in"))
            
        values = None
        try:
            values = json.loads(request.POST.keys()[0])
        except ValueError, err:
            return HttpResponseBadRequest("JSON error: " + str(err.args))
    
             
        username = values.pop('username', None)
        password = values.pop('password', None)
        
        if(username == None):
            return HttpResponseBadRequest(_("You have to provide a username"))
            
        if(password == None):
            return HttpResponseBadRequest(_("You have to provide a password"))
            
        user = django_authenticate(username=username, password=password)
            
        if user is not None:
            django_login(request, user)
            return HttpResponse(_(u"Login successfull"), status=200)
        else:
            return HttpResponse(_(u"Wrong password or username not found"),
                                status=401)
            

def logout(request):
    """
    simple logout function

    Returns:
        200 if logout successful
    """
    django_logout(request)
    return HttpResponse(_("You have successfully signed out"))

#openid authentication views
def openid_begin(request):
    """
    This function takes the openid_provider url as an
    get arguments and proceedes with the openid authentication
    prcedure
    """
    openid_op = request.GET['openid_provider']
    answ = openid_auth.preAuthenticate(openid_op,
                                        settings.OPENID_COMPLETE_URL,
                                        sreg = ((), ()),
                                        ax = ((), ())
                                        )

    request.session['id_claim'] = answ[1]
    return answ[0]
    
def openid_complete(request):
    """
    This function takes the response from the openid provider

    if the user has not logged in before with the openid it will register a
    user and connect the user with the openid claim

    if the user has logged in before then the same user is authenticated and logged
    in
    """
    user = django_authenticate(request=request,
                                claim=request.GET['openid.identity'])
  
    if(user.is_anonymous()):
        search_user_name = True
        i = 0
        while(search_user_name):
            try:
                username = "anonymous-" + str(i)
                new_user = User.objects.create_user(username=username,
                                                    password="no-pass",
                                                    email="")
                new_user.save()
                openid_auth.linkOpenID(new_user, request.GET['openid.identity'])
                new_user = django_authenticate(username=username,
                                                password="no-pass")
                search_user_name = False
            except IntegrityError:
                i = i + 1
                django.db.connection.close()
                
        django_login(request, new_user)
        
        new_user.set_unusable_password()
        new_user.save()
        
    else:
        django_login(request, user)
    
    return HttpResponseRedirect(getattr(settings, "OPENID_REDIRECT_URL", "/"))
    

#registering for an softGIS API account
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
    'allow_notifications': <optional>
    }

    if email is provided it will be confirmed with an confirmation link
    sent to the user.

    notifications is if the user wants notification of updates to the service
    to his/her email
    
    
    Returns:
        201 if successful
        400 for Bad Request
        409 for Conflict
    """
    if(request.method == "GET"):    
        return HttpResponse("")

    elif(request.method == "POST"):

        if request.user.is_authenticated() == True:
            return HttpResponseBadRequest(_("You cannot register a user when logged in"))
    
    
        values = None
        try:
            values = json.loads(request.POST.keys()[0])
        except ValueError, err:
            return HttpResponseBadRequest("JSON error: " + str(err.args))
        

        username = values.pop('username', None)
        password = values.pop('password', None)
        email = values.pop('email', None)
        allow_notifications = values.pop('allow_notifications', False)
        
        if(username == None or username == ""):
            return HttpResponseBadRequest(_(u"You have to provide a username"))
        
        if(password == None or password == ""):
            return HttpResponseBadRequest(_(u"You have to provide a password"))
        
        #create user for django auth
        user = User(username = username,
                    email = "",
                    password = password)
        user.set_password(password)
        
        try:
            user.validate_unique()
        except ValidationError, err:
            message = " "
            error_msg = []

            for desc in err.message_dict.keys():
                error_msg.append(err.message_dict[desc][0])
                
            return HttpResponse(status=409, content=message.join(error_msg))

        try:
            user.full_clean()
        except ValidationError, err:
            message = " "
            error_msg = []

            for desc in err.message_dict.keys():
                error_msg.append(err.message_dict[desc][0])
                
            return HttpResponseBadRequest(message.join(error_msg))
            
        try:
            sid = transaction.savepoint()
            user.save()
            transaction.savepoint_commit(sid)
        except IntegrityError, err:
            transaction.savepoint_rollback(sid)
            
            message = " "
            error_msg = []

            for desc in err.message_dict.keys():
                error_msg.append(err.message_dict[desc][0])
                
            return HttpResponse(status=409, content=message.join(error_msg))
        
        #add additional profile values
        static_profile_values = StaticProfileValue(user=user)
        static_profile_values.allow_notifications = allow_notifications
        static_profile_values.email = email
        static_profile_values.save()
                
        if not email == '' and not email == None:
            EmailAddress.objects.add_email(user, email)
            
        #authenticate and login
        user = django_authenticate(username=username,
                                    password=password)
        
        if user is not None and user.is_active:
            django_login(request, user)
            
        return HttpResponse(status=201)
        

def new_password(request):
    """
    This function sends new password to the given email address.
    
    Returns:
        200 if successful
        400 if email address is not confirmed
        404 if email address is not found

    """
    
    if(request.method == "POST"):
    
        request_json = json.loads(request.POST.keys()[0])
        
        email = request_json['email']
        static_user = None
        confirmed = False
 
        if not email == None and not email == '':
            try:
                static_user = \
                    StaticProfileValue.objects.get(email__exact = email)
            except ObjectDoesNotExist:
                pass

        if static_user == None:
            return HttpResponseNotFound(
                        _(u"email not found"))
        else:
            try:
                confirmed = EmailAddress.objects.get(
                                    user__exact = static_user.user).verified
            except ObjectDoesNotExist:
                pass
            
        if confirmed == False:
            return HttpResponseBadRequest(
                        _(u"Please confirm your email address before requesting a new password"))

        rnd = Random()
        
        righthand = '23456qwertasdfgzxcvbQWERTASDFGZXCVB'
        lefthand = '789yuiophjknmYUIPHJKLNM'
        
        passwordlength = 8
        
        password = ""
        
        for i in range(passwordlength):
            if i % 2:
                password += rnd.choice(righthand)
            else:
                password += rnd.choice(lefthand)
        
        subject = _('Uusi salasana pehmogis sivustolle')
        message = static_user.user.username + \
                        _(' uusi salasana on: ') + password
        
        try:
            send_mail(subject,
                        message,
                        'do_not_reply@pehmogis.fi',
                        [static_user.email])
            static_user.user.set_password(password)
            static_user.user.save()
            return HttpResponse(_(u"New password sent to ") + \
                                    static_user.email, 
                                    status=200, 
                                    content_type='text/plain')
        except BadHeaderError:
            return HttpResponseBadRequest(_(u'Invalid header found.'))
            

    return HttpResponseBadRequest(_("This URL only accepts POST requests"))
    
def change_password(request):
    """
    This function changes the user password.
    
    Returns:
        200 if successful
        400 if old or new password is not provided
        401 if current password is not correct
        403 if user is not signed in

    """
    
    if not request.user.is_authenticated():
        return HttpResponseForbidden(_(u"The request has to be made by an signed in user"))


    if(request.method == "POST"):
        
        request_json = json.loads(request.POST.keys()[0])
        
        new_password = request_json['new_password']
        old_password = request_json['old_password']

        if(old_password == None or old_password == ''):
            return HttpResponseBadRequest(_(u"You have to enter your current password"))

        if not request.user.check_password(old_password):
            return HttpResponse(_(u"Wrong password"), status=401)
        
        if(new_password == None or new_password == ''):
            return HttpResponseBadRequest(_(u"You have to provide a password"))
        
        request.user.set_password(new_password)
        request.user.save()
        
        return HttpResponse(_(u"Password changed succesfully"),
                                status=200)
        
    return HttpResponseBadRequest(_(u"This URL only accepts POST requests"))   
    
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
            if email_addr == None:
                django.db.connection.close()
                
        new_profile_value = ProfileValue(user = request.user,
                                        json_string = json.dumps(values))
        new_profile_value.save()
        
    return HttpResponse("")
        
#Views for the geometry API
def feature(request):
    """
    This function handles the feature part of the softgis REST api
    
    On GET request this function returns a geojson featurecollection
    matching the query string.
    
    On POST request this functions adds a new feature or modifies 
    the existing feature in the database.
    
    On DELETE request this function removes existing feature from 
    the database.
    
    Returns:
        200 if successful and geojson featurecollection (GET, POST)
        403 if not signed in
        400 if bad request

    """
    
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
            feature_queryset = \
                    Feature.objects.filter(user__exact = request.user)

        # transform geometries to the correct SpatialReferenceSystem
        #feature_queryset.transform(3067)

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
                property_queryset = property_queryset.filter(value_name = key,
                                                            value = value)

        
        #filter the features with wrong properties
        feature_id_list = property_queryset.values_list('feature_id', flat=True)

        # Not in use and gives database error in sqlite3
        # feature_queryset =
        #       feature_queryset.filter(id__in = list(feature_id_list))
        
        for feature in feature_queryset:
            feature_collection['features'].append(feature.geojson())

        # According to GeoJSON specification crs member
        # should be on the top-level GeoJSON object
        # get srid from the first feature in the collection
        if feature_queryset.exists():
            srid = feature_queryset[0].geometry.srid
        else:
            srid = 3067

        crs_object =  {"type": "EPSG", "properties": {"code": srid}}
        feature_collection['crs'] = crs_object
        
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
        
        feature_json = json.loads(request.POST.keys()[0])
        try:
            feature_json = json.loads(request.POST.keys()[0])
        except ValueError:
            return HttpResponseBadRequest(
                        "mime type should be application/json")

        
        identifier = None
        geometry = []
        properties = None
        category = None
        
        try:
            geometry = feature_json['geometry']
            properties = feature_json['properties']
            category = feature_json['properties']['category']
        except KeyError:
            return HttpResponseBadRequest("json requires properties"  + \
                                            "and geometry, and the" + \
                                            "properties a category value")
          
        try:
            identifier = feature_json['id']
        except KeyError:
            pass
            
        if identifier == None:
            #save a new feature if id is None
            
            #geos = GEOSGeometry(json.dumps(geometry))
            # Have to make OGRGeometry as GEOSGeometry
            # does not support spatial reference systems
            geos = OGRGeometry(json.dumps(geometry)).geos
            new_feature = None
            new_feature = Feature(geometry=geos,
                                    user=request.user,
                                    category=category)
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
            #only the feature properties is updated otherwise a
            #completely new feature should be added
            try:
                new_feature = Feature.objects.get(id__exact = identifier)
                new_property = Property(feature = new_feature,
                                        json_string = json.dumps(properties))
                new_property.save()
                
            except ObjectDoesNotExist:
                return HttpResponseBadRequest(
                            "no feature with the given id found")

        return HttpResponse(json.dumps(feature_json))


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
