from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

import sys

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json
    
      
class AuthenticationTest(TestCase):
    
    def setUp(self):
        self.client = Client()

        
    def test_registration(self):
        """
        Tests that the registration works.
        """
        #valid post
        post_content = {'username':'mike', 'password':'mikepass'}
        response = self.client.post(reverse('api_register'),
                                    json.dumps(post_content),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 201)

        #logout
        self.client.logout()

        #invalid post
        post_content = {'something':'some'}
        response = self.client.post(reverse('api_register'),
                                    json.dumps(post_content),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 400)
        
        post_content = {'username':'mike'}
        response = self.client.post(reverse('api_register'),
                                    json.dumps(post_content),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 400)
        
        post_content = {'password':'mike'}
        response = self.client.post(reverse('api_register'),
                                    json.dumps(post_content),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 400)
        
        #conflict
        post_content = {'username':'mike', 'password':'mikepass'}
        response = self.client.post(reverse('api_register'),
                                    json.dumps(post_content),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 409)

    def test_login(self):
        """
        test the login procedure
        """
        #register a user
        post_content = {'username':'testuser', 'password':'testpass'}
        response = self.client.post(reverse('api_register'),
                                    json.dumps(post_content), \
                                    content_type='application/json')
        self.assertEquals(response.status_code,
                          201,
                          'registration did not work')

        #logout after registration
        self.client.logout()
        
        #invalid login
        post_content = {'username':'some', 'password':'pass'}
        response = self.client.post(reverse('api_login'),
                                    json.dumps(post_content), 
                                    content_type='application/json')
        self.assertEquals(response.status_code, 401)
        post_content = {'username':'some', 'password':'testpass'}
        response = self.client.post(reverse('api_login'),
                                    json.dumps(post_content),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 401)
        post_content = {'username':'testuser', 'password':'pass'}
        response = self.client.post(reverse('api_login'),
                                    json.dumps(post_content),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 401)
        
        #valid login
        post_content = {'username':'testuser', 'password':'testpass'}
        response = self.client.post(reverse('api_login'),
                                    json.dumps(post_content), 
                                    content_type='application/json')
        self.assertEquals(response.status_code,
                          200,
                          'login with valid username and password did not work')
        
    def test_session(self):
        """
        This method tests the create session
        REST url.
        """
        #get the initial session key
        session_key_anonymous = self.client.get(reverse('api_session')).content
        
        #create a session
        response = self.client.post(reverse('api_session'))
        self.assertEqual(response.status_code,
                         200,
                         "The session creation through the session url did not work")
        
        
        #check that the session created is the same for all gets even if post in between
        session_key_anonymous_user = self.client.get(reverse('api_session')).content
        self.assertNotEqual(session_key_anonymous_user,
                            session_key_anonymous,
                            "The post to session url did not create a new session")
        
        #only one session can be created per anonymous user
        response = self.client.post(reverse('api_session'))
        self.assertEqual(response.status_code,
                         200,
                         "The session creation through the session url did not work")
        
        #get the possibly new session key
        session_key_anonymous_user_2 = self.client.get(reverse('api_session')).content
        
        self.assertEquals(session_key_anonymous_user,
                          session_key_anonymous_user_2,
                          "The session key is not persistent for anonymous user")
            
            
        #delete the session
        response = self.client.delete(reverse('api_session'))
        self.assertEqual(response.status_code,
                         200,
                         "The session deletion through the session url did not work")
        
        
        #check that the session created is the same for all gets even if post in between
        session_key_anonymous_user = self.client.get(reverse('api_session')).content
        self.assertNotEqual(session_key_anonymous_user,
                            session_key_anonymous,
                            "The post to session url did not create a new session for second anonymous user")
        
        #only one session can be created per anonymous user
        response = self.client.post(reverse('api_session'))
        self.assertEqual(response.status_code,
                         200,
                         "The session creation through the session url did not work second time")
        
