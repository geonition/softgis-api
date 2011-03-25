from django.contrib.auth import logout as django_logout
from django.contrib.auth import login as django_login
from django.contrib.auth import authenticate as django_authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.utils import translation

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
    'password': <required>
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
        
        if(username == None or username == ""):
            return HttpResponseBadRequest(_(u"You have to provide a username"))
        
        if(password == None or password == ""):
            return HttpResponseBadRequest(_(u"You have to provide a password"))
        
        #create user for django auth
        user = User(username = username,
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
        
        #authenticate and login
        user = django_authenticate(username=username,
                                    password=password)
        
        if user is not None and user.is_active:
            django_login(request, user)
            
        return HttpResponse(status=201)
        

def session(request):
    """
    This function creates a user with
    no password set. This enables the user
    to stay anonymous but still save values
    in other softgis apps.
    
    GET request returns the session
    POST request creates a session for anonymous user
    DELETE request ends the session
    """
    if request.method == "GET":
        return HttpResponse(request.session.session_key)
        
    elif request.method == "POST":
        if request.user.is_authenticated():
            return HttpResponse(_(u"session already created"))
            
        new_user_id = User.objects.aggregate(Max('id'))

        if(new_user_id['id__max'] == None):
            new_user_id['id__max'] = 1
        else:
            new_user_id['id__max'] = new_user_id['id__max'] + 1
        
        User.objects.create_user(str(new_user_id),'', 'passwd')
        user = django_authenticate(username=str(new_user_id), password='passwd')
        django_login(request, user)
        user.set_unusable_password()
            
        return HttpResponse(_(u"session created"))

    elif request.method == "DELETE":
        django_logout(request)
        return HttpResponse(_(u"session end"))
        
        
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
