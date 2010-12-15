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
from softgis_api.models import Feature

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
        
class ProfileValueTest(TestCase):

    def setUp(self):
        self.client = Client()
        #register a user
        post_content = {'username':'testuser-1', 'password':'testpass'}
        response = self.client.post(reverse('api_register'),
                                    json.dumps(post_content),
                                    content_type='application/json')

    
    def test_profile_values(self):
        """
        Test getting updating and making new profile values
        """
        
        #logout
        self.client.logout()

        #get values without authentication
        response = self.client.get(reverse('api_profile'))
        
        #login
        post_content = {'username':'testuser-1', 'password':'testpass'}
        response = self.client.post(reverse('api_login'),
                                    json.dumps(post_content), 
                                    content_type='application/json')
        self.assertEquals(response.status_code,
                          200,
                          'login with valid username and password did not work')

        #response = self.client.login(username='testuser', password='testpass')
        #self.assertEquals(response, True)
        
        #get all values when no values yet added to user
        response = self.client.get(reverse('api_profile'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, '[]')

        #add profile values to user
        cur_value = {"birth_year": 1980}
        response = self.client.post(reverse('api_profile'),
                                    json.dumps(cur_value),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 200)
        
        # check values in db        
        response = self.client.get(reverse('api_profile'))
        self.assertEquals(response.status_code, 200)
        
        #add profile values to user
        cur_value = {"birth_year": 1983,
                    "gender": "M",
                    "something": "no value1"}
        response = self.client.post(reverse('api_profile'),
                                    json.dumps(cur_value),
                                    content_type='application/json')

        self.assertEquals(response.status_code, 200)
        
        # check values in db        
        response = self.client.get(reverse('api_profile'))
        self.assertEquals(response.status_code, 200)
        response_json = json.loads(response.content)
        
        #add profile values to user
        cur_value = {"birth_year": 1983,
                    "gender": "M",
                    "something": "no value2",
                    "something": "no value3"}
        response = self.client.post(reverse('api_profile'),
                                    json.dumps(cur_value),
                                    content_type='application/json')
        
        self.assertEquals(response.status_code, 200)
        
        # check values in db        
        cur_value = {"birth_year": 1983,
                     "gender": "M",
                     "something": "no value3"}
        response = self.client.get(reverse('api_profile'))
        self.assertEquals(response.status_code, 200)
        response_json = json.loads(response.content)

        #send static values to rest
        static_values = {"allow_notifications": True,
                        "gender": "F",
                        "birthyear": 1980,
                        "email": ""}
        response = self.client.post(reverse('api_profile'),
                                    json.dumps(static_values),
                                    content_type='application/json')
        self.assertEquals(response.status_code,
                          200,
                          "Valid static profile values adding did not work")
        # allow_notifications as wrong type
        static_values_false = {"allow_notifications": "true",
                            "gender": 'M',
                            "birthyear": 1980,
                            "email": ""}
        response = self.client.post(reverse('api_profile'),
                                    json.dumps(static_values_false),
                                    content_type='application/json')
        #print response.status_code
        self.assertEquals(response.status_code,
                          400,
                          "a faulty allow_notifications value type did not" + \
                          "return a bad request response")
        
        # gender as wrong type
        static_values_false = {"allow_notifications": True,
                            "gender": True,
                            "birthyear": 1980,
                            "email": ""}
        response = self.client.post(reverse('api_profile'),
                                    json.dumps(static_values_false),
                                    content_type='application/json')
        self.assertEquals(response.status_code,
                          400,
                          "a faulty gender value type did not " + \
                          "return a bad request response")
        
        # birthyear as wrong type
        static_values_false = {"allow_notifications": True,
                            "gender": '',
                            "birthyear": "yyyy",
                            "email": ""}
        response = self.client.post(reverse('api_profile'),
                                    json.dumps(static_values_false),
                                    content_type='application/json')
        self.assertEquals(response.status_code,
                          400,
                          "a faulty birthyear value type did not " + \
                          "return a bad request response")
        
        # email as wrong type
        static_values_false = {"allow_notifications": False,
                            "gender": 'F',
                            "birthyear": 1980,
                            "email": "hello.wrong.email"}
        response = self.client.post(reverse('api_profile'),
                                    json.dumps(static_values_false),
                                    content_type='application/json')
        self.assertEquals(response.status_code,
                          400,
                          "a faulty email value type did not " + \
                          "return a bad request response")
       
        #email submission        
        response = self.client.post(reverse('api_profile'),
                                    json.dumps({'email':'some@some.fi'}),
                                    content_type='application/json')
                                    
        self.assertEquals(response.status_code,
                            200,
                            "email adding did not work")
        self.assertEquals(len(mail.outbox), 1)
        
        print "CONFIRMATION EMAIL SENT SUPPOSED TO PRINT THE EMAIL:"
        print mail.outbox[0].body
                
        #change the email  
        response = self.client.post(reverse('api_profile'),
                                    json.dumps({'email':'some@other.fi'}),
                                    content_type='application/json')
                                    
        self.assertEquals(response.status_code,
                            200,
                            "email adding did not work")
        self.assertEquals(len(mail.outbox), 2)
        
        
        
class GeoApiTest(TestCase):

    def setUp(self):
        self.client = Client()
        #register a user
        post_content = {'username':'testuser', 'password':'testpass'}
        response = self.client.post(reverse('api_register'),
                                    json.dumps(post_content),
                                    content_type='application/json')
    
    def test_feature(self):
        
        #login 
        response = self.client.login(username='testuser', password='testpass')
    
        #feature without id without category
        geojson_feature = {"type": "Feature",
                            "geometry": {"type":"Point",
                                        "coordinates":[100, 200]},
                            "properties": {"some_prop":"value"}}
        
        #add category
        geojson_feature['properties']['category'] = "home"
        
        response = self.client.post(reverse('api_feature'),
                                    json.dumps(geojson_feature),
                                    content_type='application/json')
                                    
        self.assertEquals(response.status_code, 200)
        
        #the feature should now have an id but otherwise be the same
        response_feature = json.loads(response.content)
        identifier = response_feature['id']
        
        #update the feature
        geojson_feature['id'] = identifier
        geojson_feature['properties']['added_value'] = 1000
        geojson_feature['properties']['category'] = "pos_aesthetic"
        geojson_feature['properties'].pop("some_prop", None)
       
       
        response = self.client.post(reverse('api_feature'),
                                    json.dumps(geojson_feature),
                                    content_type='application/json')
        
        
        response_feature = json.loads(response.content)
        
        self.assertEquals(response_feature['id'], identifier)
        self.assertEquals(response_feature['properties']['added_value'], 1000)
        self.assertEquals(response_feature['properties']['category'],
                        "pos_aesthetic")
        
        #getting all features for this user should contain the
        #current feature submitted
        response = self.client.get(reverse('api_feature'))
        response_feature = json.loads(response.content)

        #delete the feature using identifier above
        response = self.client.delete(reverse('api_feature') \
                                        + '?id=' + str(identifier))
        self.assertEquals(response.status_code, 200, "Delete failed")

        #delete the feature using invalid id above
        response = self.client.delete(reverse('api_feature') + '?id=15555')
        
class ProfileValueDBTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 
                                            'some@somewhere.com', 
                                            'password')
    
    
    def test_profile_value(self):
        #TODO
        pass
                
class FeatureDBTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 
                                            'some@somewhere.com', 
                                            'password')
        self.poly = GEOSGeometry('POLYGON(( 10 10,' + \
                                            '10 20,' + \
                                            '20 20,' + \
                                            '20 15,' + \
                                            '10 10))')
        self.point = GEOSGeometry('POINT(10 10)')

    def test_feature(self):
        feat1 = Feature(geometry = self.point,
                       user = self.user)
        #save and check create_time
        feat1.save()
        self.assertNotEqual(feat1.create_time,
                            None,
                            "create_time for feature should be set")
        
        #delete and check expire_time
        feat1.delete()
        self.assertNotEqual(feat1.expire_time,
                            None,
                            "expire_time for feature should be set")
        
        feat2 = Feature(geometry = self.point,
                       user = self.user)
        feat2.save()
        
        #query all should contain both features saved
        feature_queryset = Feature.objects.all()
        self.assertEquals(feature_queryset.count(), 
                            2, 
                            "added features removed from database")
        
        #return the latest feature
        latest_feature = feature_queryset.latest('create_time')
        self.assertEquals(feat2, 
                            latest_feature, 
                            "latest feature is not the last saved feature")
        
        #retreive the latest deleted feature
        latest_deleted_feature = feature_queryset.latest('expire_time')
        self.assertEquals(feat1, 
                            latest_deleted_feature, 
                            "latest deleted feature" + \
                            "is not the last deleted feature")
                            
    
    def test_property(self):
        #TODO
        pass
        
