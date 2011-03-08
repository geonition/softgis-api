from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth import logout as django_logout
from django.contrib.auth import login as django_login
from django.contrib.auth import authenticate as django_authenticate
from models import Feature
from models import Property

import sys
import settings

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json

class FeatureTest(TestCase):
    """
    This class test the feature application.
    """
    
    def setUp(self):
        self.client = Client()
        
        #setup a testuser
        User.objects.create_user('testuser','', 'passwd')
        User.objects.create_user('testuser2','', 'passwd')
        
        
    def test_feature(self):
        """
        Black box testing for REST urls
        """
        #login testuser
        self.client.login(username='testuser', password='passwd')
        
        #get the features
        response = self.client.get(reverse('api_feature'))
        response_dict = json.loads(response.content)

        #check for geojson type
        self.assertEquals(response_dict.get('type', ''),
                          "FeatureCollection",
                          "The geojson does not seem to be valid," + \
                          " get feature should return FeatureCollection type")
        #check for empty feature array
        self.assertEquals(response_dict.get('features',''),
                          [],
                          "The featurecollection should be empty")
        
        #test posting
        #geojson feature for testing
        geojson_feature = {"type": "Feature",
                            "geometry": {"type":"Point",
                                        "coordinates":[100, 200]},
                            "properties": {"some_prop":"value"}}
        
        response = self.client.post(reverse('api_feature'),
                                    json.dumps(geojson_feature),
                                    content_type='application/json')
        
        response_dict = json.loads(response.content)
        self.assertNotEquals(response_dict.get('id',-1),
                            -1,
                            "The returned feature from a post did not contain an identifier(id)")
        
        #update a property of the feature
        geojson_feature['id'] = 1
        geojson_feature['properties']['some_prop'] = 'new value'
        response = self.client.put(reverse('api_feature'),
                                   json.dumps(geojson_feature),
                                   content_type="application/json")
        self.assertEquals(response.status_code,
                          200,
                          "Updating a feature did not work")
               
        #update a property of the feature
        geojson_feature['id'] = 1
        geojson_feature['properties']['some_prop'] = 'new value'
        response = self.client.put(reverse('api_feature'),
                                   json.dumps(geojson_feature),
                                   content_type="application/json")
        self.assertEquals(response.status_code,
                          200,
                          "Updating a feature did not work")
        
        #delete the feature
        id = response_dict.get('id')
        geojson_feature = {"type": "Feature",
                           "id": id}
        ids = []
        ids.append(id)
        
        response = self.client.delete(reverse('api_feature')+"?ids="+json.dumps(ids))
        
        self.assertEquals(response.status_code,
                          200,
                          "deletion of feature with id %i did not work" % id)
        
        #delete not existing feature
        response = self.client.delete(reverse('api_feature')+"?ids="+json.dumps(ids))
        
        self.assertEquals(response.status_code,
                          404,
                          "deletion of a non existing feature did not return NotFound")
        """
store the inserted IDs
"""
        ids = []
        
        geojson_feature = {"type": "Feature",
                            "geometry": {"type":"Point",
                                        "coordinates":[100, 200]},
                            "properties": {"some_prop":"value"}}
        
        response = self.client.post(reverse('api_feature'),
                                    json.dumps(geojson_feature),
                                    content_type='application/json')
        
        response_dict = json.loads(response.content)
        
        self.assertNotEquals(response_dict.get('id',-1),
                    -1,
                    "The returned feature from a post did not contain an identifier(id)")
        
        ids.append(response_dict.get('id'))
        
        #2nd ID
        geojson_feature = {"type": "Feature",
                    "geometry": {"type":"Point",
                                "coordinates":[200, 200]},
                    "properties": {"some_prop":"value"}}
        
        response = self.client.post(reverse('api_feature'),
                                    json.dumps(geojson_feature),
                                    content_type='application/json')
        
        response_dict = json.loads(response.content)
        
        self.assertNotEquals(response_dict.get('id',-1),
                    -1,
                    "The returned feature from a post did not contain an identifier(id)")
        
        ids.append(response_dict.get('id'))
        
        #3rd ID
        geojson_feature = {"type": "Feature",
                    "geometry": {"type":"Point",
                                "coordinates":[300, 300]},
                    "properties": {"some_prop":"value"}}
        
        response = self.client.post(reverse('api_feature'),
                                    json.dumps(geojson_feature),
                                    content_type='application/json')
        
        response_dict = json.loads(response.content)
        
        self.assertNotEquals(response_dict.get('id',-1),
                    -1,
                    "The returned feature from a post did not contain an identifier(id)")
        
        ids.append(response_dict.get('id'))
        
        #delete a FeatureCollection once
        response = self.client.delete(reverse('api_feature')+"?ids="+json.dumps(ids))
        
        self.assertEquals(response.status_code,
                          200,
                          "deletion of feature collection with ids " + str(ids) +" did not work")
        
        idn = []
        idn.append(ids[0])
        
        #test if deleted
        response = self.client.delete(reverse('api_feature')+"?ids="+json.dumps(idn))
        
        self.assertEquals(response.status_code,
                          404,
                          "deletion of feature previous feature did not work")
        idn = []
        idn.append(ids[1])
        
        response = self.client.delete(reverse('api_feature')+"?ids="+json.dumps(idn))
        
        self.assertEquals(response.status_code,
                          404,
                          "deletion of feature previous feature did not work")
        idn = []
        idn.append(ids[2])
        
        response = self.client.delete(reverse('api_feature')+"?ids="+json.dumps(idn))
        
        self.assertEquals(response.status_code,
                          404,
                          "deletion of feature previous feature did not work")
        
        #send delete without ids
        response = self.client.delete(reverse('api_feature'))
        
        self.assertEquals(response.status_code,
                          404,
                          "feature deletion without id did not return 404 not found")
        
    def test_mongodb(self):
        USE_MONGODB = getattr(settings, "USE_MONGODB", False)
        
        #if mongodb is not in use do not run the tests
        if not USE_MONGODB: 
            return None
        
        
        #save some features and properties for testing
        
        
                
        
        