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
from api.models import Feature
from api.models import Property
from api.models import ProfileValue

import unittest
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
        post_content = {'username':'toffe','password':'toffepass'}
        response = self.client.post(reverse('api_register'), post_content, \
                                    content_type='application/json')
        self.assertEquals(response.status_code, 201)

        #logout
        self.client.logout()

        #invalid post
        post_content = {'something':'some'}
        response = self.client.post(reverse('api_register'), post_content, \
                                    content_type='application/json')
        self.assertEquals(response.status_code, 400)
        
        post_content = {'username':'toffe'}
        response = self.client.post(reverse('api_register'), post_content, \
                                    content_type='application/json')
        self.assertEquals(response.status_code, 400)
        
        post_content = {'password':'some'}
        response = self.client.post(reverse('api_register'), post_content, \
                                    content_type='application/json')
        self.assertEquals(response.status_code, 400)
        
        #conflict
        post_content = {'username':'toffe','password':'toffepass'}
        response = self.client.post(reverse('api_register'), post_content, \
                                    content_type='application/json')
        self.assertEquals(response.status_code, 409)

    def test_login(self):
        """
        test the login procedure
        """
        #register a user
        post_content = {'username':'testuser','password':'testpass'}
        response = self.client.post(reverse('api_register'), post_content, \
                                    content_type='application/json')
        self.assertEquals(response.status_code, 201,
                          'registration did not work')

        #logout after registration
        self.client.logout()
        
        #invalid login
        post_content = {'username':'some','password':'pass'}
        response = self.client.post(reverse('api_login'), post_content, \
                                    content_type='application/json')
        self.assertEquals(response.status_code, 401)
        post_content = {'username':'some','password':'testpass'}
        response = self.client.post(reverse('api_login'), post_content, \
                                    content_type='application/json')
        self.assertEquals(response.status_code, 401)
        post_content = {'username':'testuser','password':'pass'}
        response = self.client.post(reverse('api_login'), post_content, \
                                    content_type='application/json')
        self.assertEquals(response.status_code, 401)
        
        #valid login
        post_content = {'username':'testuser','password':'testpass'}
        response = self.client.post(reverse('api_login'), post_content, \
                                    content_type='application/json')
        self.assertEquals(response.status_code, 200,
                          'login with valid username and password did not work')
        
class ProfileValueTest(TestCase):

    def setUp(self):
        self.client = Client()
        #register a user
        post_content = {'username':'testuser', 'password':'testpass'}
        response = self.client.post(reverse('api_register'), post_content, \
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
        response = self.client.login(username='testuser', password='testpass')
        self.assertEquals(response, True)
        
        #get all values when no values yet added to user
        response = self.client.get(reverse('api_profile'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, '[{}]')

        #add profile values to user
        cur_value = '{"birth_year": 1980}'
        response = self.client.post(reverse('api_profile'), \
                                    eval(cur_value), \
                                    content_type='application/json')
        self.assertEquals(response.status_code, 200)
        
        # check values in db        
        response = self.client.get(reverse('api_profile'))
        self.assertEquals(response.status_code,200)
        
        #add profile values to user
        cur_value = '{"birth_year": 1983,"gender": "M", "something": "no value1"}'
        response = self.client.post(reverse('api_profile'), eval(cur_value), \
                                    content_type='application/json')
        self.assertEquals(response.status_code, 200)
        
        # check values in db        
        response = self.client.get(reverse('api_profile'))
        self.assertEquals(response.status_code,200)
        response_json = json.loads(response.content)
        
        #add profile values to user
        cur_value = '{"birth_year": 1983,"gender": "M", "something": "no value2", "something": "no value3"}'
        response = self.client.post(reverse('api_profile'), \
                                    eval(cur_value), \
                                    content_type='application/json')
        
        self.assertEquals(response.status_code, 200)
        
        # check values in db        
        cur_value = '{"birth_year": 1983,"gender": "M", "something": "no value3"}'
        response = self.client.get(reverse('api_profile'))
        self.assertEquals(response.status_code,200)
        response_json = json.loads(response.content)
        
        #email submission        
        response = self.client.post(reverse('api_profile'), \
                                            {'email':'some@some.fi'}, \
                                    content_type='application/json')
        self.assertEquals(response.status_code, 200, "email adding did not work")
        self.assertEquals(len(mail.outbox), 1)
        
        print "CONFIRMATION EMAIL SENT SUPPOSED TO PRINT THE EMAIL:"
        print mail.outbox[0].body
        
        
class GeoApiTest(TestCase):

    def setUp(self):
        self.client = Client()
        #register a user
        post_content = {'username':'testuser', 'password':'testpass'}
        response = self.client.post(reverse('api_register'), \
                                    post_content, \
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
        
        response = self.client.post(reverse('api_feature'),\
                                    geojson_feature, \
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
       
       
        response = self.client.post(reverse('api_feature'),\
                                    geojson_feature, \
                                    content_type='application/json')
        
        
        response_feature = json.loads(response.content)
        
        self.assertEquals(response_feature['id'], identifier)
        self.assertEquals(response_feature['properties']['added_value'], 1000)
        self.assertEquals(response_feature['properties']['category'], "pos_aesthetic")  
        
        #getting all features for this user should contain the current feature submitted
        response = self.client.get(reverse('api_feature'))
        response_feature = json.loads(response.content)

        #delete the feature using identifier above
        response = self.client.delete(reverse('api_feature') + '?id=' + str(identifier))
        self.assertEquals(response.status_code, 200, "Delete failed")

        #delete the feature using invalid id above
        response = self.client.delete(reverse('api_feature') + '?id=15555')
        
class ProfileValueDBTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', \
                                            'some@somewhere.com', \
                                            'password')
    
    
    def test_profile_value(self):
        value1 = ProfileValue(user=self.user, \
                             value_name="test_name", \
                             value="test_value")
        value2 = ProfileValue(user=self.user, \
                             value_name="something", \
                             value="test_value")
        value3 = ProfileValue(user=self.user, \
                             value_name="test_name", \
                             value="new_value")
        value4 = ProfileValue(user=self.user, \
                             value_name="test_name", \
                             value="new_value")
        value5 = ProfileValue(user=self.user, \
                             value_name="other_name", \
                             value="other_value")
        
        value1.save()
        value2.save()
        value3.save()
        value4.save()
        value5.save()
        
        #check the DB
        value_queryset = ProfileValue.objects.filter(user__exact = self.user)
        
        #together there should be 4 profile values
        self.assertEquals(value_queryset.count(), \
                            4, \
                            "There should be 4 ProfileValues in the DB")
                            
        value_queryset = ProfileValue.objects.filter(user__exact = self.user, \
                                                    expire_time__isnull = True)
        
        #together there should be 3 current profile values
        self.assertEquals(value_queryset.count(), \
                            3, \
                            "There should be 3 current ProfileValues in the DB")
                            
        value_queryset = ProfileValue.objects.filter(user__exact = self.user, \
                                                    expire_time__isnull = False)
        
        #together there should be 1 old profile value
        self.assertEquals(value_queryset.count(), \
                            1, \
                            "There should be 1 old ProfileValue in the DB")
                
class FeatureDBTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', \
                                            'some@somewhere.com', \
                                            'password')
        self.poly = GEOSGeometry('POLYGON(( 10 10, 10 20, 20 20, 20 15, 10 10))')
        self.point = GEOSGeometry('POINT(10 10)')

    def test_feature(self):
        feat1 = Feature(geometry = self.point,
                       user = self.user)
        #save and check create_time
        feat1.save()
        self.assertNotEqual(feat1.create_time, None, "create_time for feature should be set")
        
        #delete and check expire_time
        feat1.delete()
        self.assertNotEqual(feat1.expire_time, None, "expire_time for feature should be set")
        
        feat2 = Feature(geometry = self.point,
                       user = self.user)
        feat2.save()
        
        #query all should contain both features saved
        feature_queryset = Feature.objects.all()
        self.assertEquals(feature_queryset.count(), \
                            2, \
                            "added features removed from database")
        
        #return the latest feature
        latest_feature = feature_queryset.latest('create_time')
        self.assertEquals(feat2, \
                            latest_feature, \
                            "latest feature is not the last saved feature")
        
        #retreive the latest deleted feature
        latest_deleted_feature = feature_queryset.latest('expire_time')
        self.assertEquals(feat1, \
                            latest_deleted_feature, \
                            "latest deleted feature is not the last deleted feature")
                            
    
    def test_property(self):
        feat = Feature(geometry = self.point,
                       user = self.user)
        #save and check create_time
        feat.save()
        #create properties
        prop1 = Property(feature=feat, \
                         value_name="test_name", \
                         value="test_value")
        prop2 = Property(feature=feat, \
                         value_name="value_name", \
                         value="value")
        prop3 = Property(feature=feat, \
                         value_name="something", \
                         value="say yes")
        prop4 = Property(feature=feat, \
                         value_name="test_name", \
                         value="test_value_new")
        prop5 = Property(feature=feat, \
                         value_name="value_name", \
                         value="value")
        
        # save prop1 and check that it is in the DB
        prop1.save()
        feature_properties = Property.objects.filter(feature__exact = feat)
        self.assertEquals(feature_properties[0], prop1, "property was not saved")
        
        # save the rest of the properties
        prop2.save()
        prop3.save()
        prop4.save()
        prop5.save()
        
        #check current properties
        feature_properties = Property.objects.filter(feature__exact = feat, \
                                                    expire_time__isnull = False)
                        
        #properties where expire time has been set should be 1                          
        self.assertEquals(feature_properties.count(), \
                          1, \
                          "no expire time set to updated property")
        
        
        feature_properties = Property.objects.filter(feature__exact = feat, \
                                                    expire_time__isnull = True)
                        
        #properties where expire time is not set should be 3                          
        self.assertEquals(feature_properties.count(), \
                          3, \
                          "wrong amount of current properties")
        
        
        feature_properties = Property.objects.filter(feature__exact = feat)
                        
        # all together there should be 4 properties set                          
        self.assertEquals(feature_properties.count(), \
                          4, \
                          "wrong amount of properties")
        
