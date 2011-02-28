# -*- coding: utf-8 -*-
"""
This file includes all the tests to test the api functionallity.

"""

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.gis.geos import GEOSGeometry
from django.core import mail
from softgis_email.models import EmailConfirmation
from softgis_email.models import EmailAddress

import sys

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json
    
class EmailTest(TestCase):

    def setUp(self):
        self.client = Client()
	self.user = None
	
        #register a user
        post_content = {'username':'cristian1000',
                        'password':'cristi'}
                        
        response = self.client.post(reverse('api_register'),
                                    json.dumps(post_content),
                                    content_type='application/json')

    
    def test_email_update(self):
        """
        Test registering new email
        """
        
        #case 1 - no email sent
        post_content = {"email" : ""}
        
        response = self.client.post(reverse('api_manage_email'),
                                    json.dumps(post_content),
                                    content_type='application/json')
        
	self.assertEquals(response.status_code,
			    400,
			    "trying to set empty email address")

    def test_email_update_with_data(self):
        post_content = {"email" : "test@aalto.fi"}
        response = self.client.post(reverse('api_manage_email'),
                                    json.dumps(post_content),
                                    content_type='application/json')

        #Test if confirmation email is sent
        self.assertEquals(len(mail.outbox), 1, "Confirmation email not sent")

        #confirm the email

	emailAddress = EmailAddress.objects.get(email = "test@aalto.fi")
	emailConfirmation = EmailConfirmation.objects.get(email_address = emailAddress)
	
	response = self.client.get(reverse('api_emailconfirmation', args=[emailConfirmation.confirmation_key]))	
        self.assertEquals(response.status_code,
            200,
            "the email address confirmation url is not working")
        response = self.client.get(reverse('api_manage_email'))
	responsejson = json.loads(response.content)

	self.assertEquals(responsejson.get('email'), "test@aalto.fi", "The email obtain using get is not ok")
	
	#delete the email and test again the GET
	response = self.client.delete(reverse('api_manage_email'))
	
        self.assertEquals(response.status_code,
			    200,
			    "the email address delete not working")
        
	response = json.loads(self.client.get(reverse('api_manage_email')).content)
	
	self.assertEquals(response.get('email'), "", "The email obtain using GET after delete is not an empty string")
	
	
        """
        #logout
        self.client.logout()
        
        # Test with correct but not confirmed email
        response = self.client.post(reverse('api_new_password'),
                                    json.dumps({'email':'some@some.fi'}),
                                    content_type='application/json')
                                    
                                    
        self.assertEquals(response.status_code,
                            400,
                            "not sending non-confirmed email did not work")

        
        self.assertEquals(len(mail.outbox), 1,
                          "Mail sent even not confirmed email address")
        
        # Test with non-existing email 
        response = self.client.post(reverse('api_new_password'),
                                    json.dumps({'email':'example@example.com'}),
                                    content_type='application/json')
                                    
        self.assertEquals(response.status_code,
                            404,
                            "test with non-existing email did not work")
 
        self.assertEquals(len(mail.outbox),
                          1,
                          "Mail sent to non-existing email address")

        #confirm the email
        key = EmailConfirmation.objects.get(
                email_address__email__exact = 'some@some.fi').confirmation_key
        url = '/confirm_email/' + key + '/'
        self.client.get(url)
        
        #Test with confirmed email
        response = self.client.post(reverse('api_new_password'),
                            json.dumps({'email':'some@some.fi'}),
                            content_type='application/json')
                            
        self.assertEquals(response.status_code, 
                          200,
                          "Test with confirmed email failed")

        self.assertEquals(len(mail.outbox), 2, "new password email not sent")
        
        #test login with new password
        #parse new password, this will be broken if mail body is changed
        new_password = mail.outbox[1].body.rpartition(' ')[2]
        
        post_content = {'username':'testuser-1', 'password': new_password}
        response = self.client.post(reverse('api_login'),
                                    json.dumps(post_content), 
                                    content_type='application/json')
        
        self.assertEquals(response.status_code,
                          200,
                          'login with new password did not work')
        
        """
