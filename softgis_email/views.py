from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotFound
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.utils import translation
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ValidationError
from django.core.validators import email_re
from softgis_email.models import EmailConfirmation
from softgis_email.models import EmailAddress
import json

# set the ugettext _ shortcut
_ = translation.ugettext

# View used for confirming a user email using the confirmation key
def confirm_email(request, confirmation_key):
    confirmation_key = confirmation_key.lower()
    
    
    email_address = EmailConfirmation.objects.confirm_email(confirmation_key)
    return render_to_response("emailconfirmation/confirm_email.html", {
        "email_address": email_address,
    }, context_instance=RequestContext(request))
    
    
        
#Views used for managing the email
def email(request):
    """
    This function handles the email managing part of the softgis REST api
    
    On GET request this function returns the email for a userid
    matching the query string.
    
    On POST request this functions adds a new email or modifies 
    the existing email in the database for the specified user.
    
    On DELETE request this function removes existing email from 
    the database for a specified user.
    
    Returns:
        200 if successful and user exists
        400 if bad request
        404 if user not found

    """
    #check if authenticated
    if not request.user.is_authenticated():
        return HttpResponseForbidden(_(u"You haven't signed in."))
    
    user = request.user
    
    
    
        
    if(request.method == "GET"):
        #return user email in json format
        json_data = json.dumps({"email":user.email})
        return HttpResponse(json_data, mimetype="application/json")
                
    elif(request.method == "POST"):

        email = json.loads(request.POST.keys()[0]).get("email", "")
  
       
        #check if email was provided
        if (email == "" or email == None):
            return HttpResponseBadRequest(
                    _(u"Expected argument email was not provided"))


        
        """ Test if the email address is the same as existing one. If so don't send the confirmation email """
        if (user.email != email):
          
            #validate email
            if not email_re.match(email):
                 return HttpResponseBadRequest(
                    _(u"Email is not valid"))
                
            """ Send confirmation email"""
            EmailAddress.objects.add_email(user, email)

            return HttpResponse(_(u"A confirmation email was sent to your new email address. Follow the intructions in the email to complete the registration."),
                            status=200)
        
        return HttpResponse(_(u"You already have this email address assigned to you"),
                            status=200)    
       
    elif (request.method  == "DELETE"):

                
        #reset email and save
        user.email = ""

        EmailAddress.objects.filter(user = user).delete()
    
        #EmailConfirmation.objects.filter(email_address in emailAddersses).delete()
        #EmailAddress.objects.filter(user = user).delete()
        
        #should delete user's coresponding EmailAddress and EmailConfirmation models
        """if (not user.EmailAddress == None) and (not user.EmailAddress.EmailConfirmation == None):
            user.EmailAddress.EmailConfirmation.delete()
            
        if not user.EmailAddress == None:
            user.EmailAddress.delete()
        """
        #save changes
        user.save()
        
        return HttpResponse(_(u"Email deleted succesfully"),
                            status=200)
        

                
             
        
    
        
    
    
