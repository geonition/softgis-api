from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth import logout as django_logout
from django.contrib.auth import login as django_login

import time
import sys
import settings
import datetime

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json
    


class ProfileTest(TestCase):
    """
    This class tests the profile app REST
    """
    
    def setUp(self):
        self.client = Client()
        
        user = User.objects.create_user('profileuser', '', 'passwd')
        user.save()
    
    
    def test_profile(self):
        user = User.objects.create_user('profiletestuser', '', 'passwd')
        user.save() #something wrong sith setup?
        self.client.login(username='profiletestuser', password='passwd')
        
        profile_dict = {
            'age': 30
        }
        
        self.client.post(reverse('api_profile'),
                         json.dumps(profile_dict),
                         content_type="application/json")
        
        response = self.client.get(reverse('api_profile'))
        
        response_dict = json.loads(response.content)
        
        self.assertEquals(response_dict[0]['age'],
                          30,
                          "The profile query did not return the right json")
        
    def test_mongodb(self):
        USE_MONGODB = getattr(settings, "USE_MONGODB", False)
        
        #if mongodb is not in use do not run the tests
        if USE_MONGODB:
            
            user = User.objects.create_user('profilemongo', '', 'passwd')
            user.save() #something wrong sith setup?
        
            self.client.login(username='profilemongo', password='passwd')
            
            #save some values into the database
            profile_dict = {
                "age": 30,
                "gender": "M",
                "happy": True
            }
            
            response = self.client.post(reverse('api_profile'),
                                     json.dumps(profile_dict),
                                     content_type='application/json')
            
            
            #retrieve object out of scope age__max=29
            response = self.client.get(reverse('api_profile') + "?age__max=29")
          
            response_dict = json.loads(response.content)
            
            self.assertEquals(len(response_dict),
                              0,
                              "The profile query should have returned 0 profiles")
            
            #retrieve object out of scope age__min=45
            response = self.client.get(reverse('api_profile') + "?age__min=45")
            response_dict = json.loads(response.content)
            self.assertEquals(len(response_dict),
                              0,
                              "The profile query should have returned 0 profile")
            
            #retrieve one object age=30
            response = self.client.get(reverse('api_profile') + "?age=30")
            response_dict = json.loads(response.content)
            self.assertEquals(len(response_dict),
                              1,
                              "The profile query should have returned 1 profile")
            
            #retrieve objects in scope age__min=41&age__max=45
            response = self.client.get(reverse('api_profile') + "?age__min=29&age__max=31")
            response_dict = json.loads(response.content)
            self.assertEquals(len(response_dict),
                              1,
                              "The profile query should have returned 1 profile")
            
            
            #retrieve objects with string value
            response = self.client.get(reverse('api_profile') + "?gender=%s" % "M")
            response_dict = json.loads(response.content)
            self.assertEquals(len(response_dict),
                              1,
                              "The profile query should have returned 1 profile")

            
            #retrieve objects with boolean value
            response = self.client.get(reverse('api_profile') + "?happy=true")
            response_dict = json.loads(response.content)
            self.assertEquals(len(response_dict),
                              1,
                              "The profile query should have returned 1 profile")
        
    def test_history(self):
        
        user = User.objects.create_user('profilehistory', '', 'passwd')
        user.save() #something wrong sith setup?
        
        res = self.client.login(username='profilehistory', password='passwd')
       
        
        #save some values into the database
        profile_dict = {
            "age": 30,
            "gender": "M",
            "happy": True
        }
        
        profile_dict2 = {
            "age": 35,
            "gender": "F",
            "happy": False
        }
        
        before_create = datetime.datetime.now()
        
        time.sleep(1) #wait a second to get smart queries
        
        response = self.client.post(reverse('api_profile'),
                                json.dumps(profile_dict),
                                content_type='application/json')
        
        self.assertEquals(200,
                          response.status_code,
                          "Saving of profile did not return 200 OK")
        
        #wait a little bit to get difference
        time.sleep(1)
        after_create = datetime.datetime.now()
        time.sleep(1)
        
        #update
        response = self.client.post(reverse('api_profile'),
                                json.dumps(profile_dict2),
                                content_type='application/json')
        
        self.assertEquals(200,
                          response.status_code,
                          "Update of profile did not return 200 OK")
        
        #delete one and check that the next delete does not affect it
        time.sleep(1)
        after_update = datetime.datetime.now()
        
        #start querying
        
        response = self.client.get(reverse('api_profile') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (before_create.year,
                                                            before_create.month,
                                                            before_create.day,
                                                            before_create.hour,
                                                            before_create.minute,
                                                            before_create.second))
        
        response_dict = json.loads(response.content)
        
        
        self.assertEquals(response_dict,
                          [],
                          "A profile query before created profile did not return empty list")
        
        response = self.client.get(reverse('api_profile') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (after_create.year,
                                                            after_create.month,
                                                            after_create.day,
                                                            after_create.hour,
                                                            after_create.minute,
                                                            after_create.second))
        
        response_dict = json.loads(response.content)
        
        self.assertEquals(response_dict[0]['age'],
                          profile_dict['age'],
                          "The returned dict before update was not correct")
        
        self.assertEquals(response_dict[0]['gender'],
                          profile_dict['gender'],
                          "The returned dict before update was not correct")
        
        self.assertEquals(response_dict[0]['happy'],
                          profile_dict['happy'],
                          "The returned dict before update was not correct")
        
        response = self.client.get(reverse('api_profile') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (after_update.year,
                                                            after_update.month,
                                                            after_update.day,
                                                            after_update.hour,
                                                            after_update.minute,
                                                            after_update.second))
        
        response_dict = json.loads(response.content)
        
        self.assertEquals(response_dict[0]['age'],
                          profile_dict2['age'],
                          "The returned dict after update was not correct")
        
        self.assertEquals(response_dict[0]['gender'],
                          profile_dict2['gender'],
                          "The returned dict after update was not correct")
        
        self.assertEquals(response_dict[0]['happy'],
                          profile_dict2['happy'],
                          "The returned dict after update was not correct")
        
        #query with time__now=true should only reutrn the valid profile value
        response = self.client.get(reverse('api_profile') + \
                                           "?time__now=true")
                                           
        response_dict = json.loads(response.content)
        
        self.assertEquals(response_dict[0]['age'],
                          profile_dict2['age'],
                          "time__now=true as parameter did not return the valid profile")
        
        self.assertEquals(response_dict[0]['gender'],
                          profile_dict2['gender'],
                          "time__now=true as parameter did not return the valid profile")
        
        self.assertEquals(response_dict[0]['happy'],
                          profile_dict2['happy'],
                          "time__now=true as parameter did not return the valid profile")
        
        
        #query with time__now=false should return both profiles
        response = self.client.get(reverse('api_profile') + \
                                           "?time__now=false")
                                           
        response_dict = json.loads(response.content)

        self.assertEquals(len(response_dict),
                          2,
                          "time__now=false as parameter did not return both profiles")
"""    
    def test_empty_profile(self):
        user = User.objects.create_user('profiletestuser', '', 'passwd')
        user.save() #something wrong sith setup?
        self.client.login(username='profiletestuser', password='passwd')
        
        profile_dict = {}
        

        self.client.post(reverse('api_profile'),
                         json.dumps(profile_dict),
                         content_type="application/json")
        
        response = self.client.get(reverse('api_profile'))
        
        self.assertEquals(response.status_code,
                          400,
                          "The profile application can save empty profiles")


        profile_dict = ""
        self.client.post(reverse('api_profile'),
                         profile_dict,
                         content_type="application/json")
       
        response = self.client.get(reverse('api_profile'))
        
        self.assertEquals(response.status_code,
                          400,
                          "The profile application can save empty profiles")
"""

