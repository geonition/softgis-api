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
import datetime
import time

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json

#change the collection name so that the production will not be polluted
Property.mongodb_collection_name = 'test'
        
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
        
        #save featurecollection
        featurecollection = {
            "type": "FeatureCollection",
            "features": []
        }
        featurecollection['features'].append(
            {"type": "Feature",
            "geometry": {"type":"Point",
                        "coordinates":[200, 200]},
            "properties": {"some_prop":"value"}})
        featurecollection['features'].append(
            {"type": "Feature",
            "geometry": {"type":"Point",
                        "coordinates":[300, 250]},
            "properties": {"some_prop":40}})
        featurecollection['features'].append(
            {"type": "Feature",
            "geometry": {"type":"Point",
                        "coordinates":[100, 300]},
            "properties": {"some_prop": True}})
        featurecollection['features'].append(
            {"type": "Feature",
            "geometry": {"type":"Point",
                        "coordinates":[100, 300]},
            "properties": {"some_prop": None}})
        
        response = self.client.post(reverse('api_feature'),
                                    json.dumps(featurecollection),
                                    content_type='application/json')
        
        #all returned feature should have an id
        for feature in json.loads(response.content)['features']:
            self.assertTrue(feature.has_key('id'),
                            "The returned feature in FeatureCollection " + \
                            "did not have an id")
        
    def test_mongodb(self):
        USE_MONGODB = getattr(settings, "USE_MONGODB", False)
        
        #if mongodb is not in use do not run the tests
        if USE_MONGODB:
            
            self.client.login(username='testuser', password='passwd')
            #save some values into the database
            geojson_feature = {
                "type": "FeatureCollection",
                "features": [
                    {"type": "Feature",
                    "geometry": {"type":"Point",
                                "coordinates":[200, 200]},
                    "properties": {"some_prop":"value"}},
                    {"type": "Feature",
                    "geometry": {"type":"Point",
                                "coordinates":[200, 200]},
                    "properties": {"some_prop": 40}},
                    {"type": "Feature",
                    "geometry": {"type":"Point",
                                "coordinates":[200, 200]},
                    "properties": {"some_prop": 40}},
                    {"type": "Feature",
                     "geometry": {"type":"Point",
                                "coordinates":[200, 200]},
                     "properties": {"some_prop": True}},
                    {"type": "Feature",
                     "geometry": {"type":"Point",
                                "coordinates":[200, 200]},
                     "properties": {"some_prop": 42}}
                    ]
            }
            
            response = self.client.post(reverse('api_feature'),
                                     json.dumps(geojson_feature),
                                     content_type='application/json')
            
            #find should return 2 results
            self.assertEquals(Property.mongodb.find({'some_prop': 40}).count(),
                           2,
                           "The mongodb find did not return 2 objects")
            
            #range should return 3
            self.assertEquals(Property.mongodb.find_range('some_prop', 39, 41).count(),
                           2,
                           "The mongodb find_ramge did not return 2 objects")
            
            
            #range should return 1
            self.assertEquals(Property.mongodb.find_range('some_prop', 41, 43).count(),
                           1,
                           "The mongodb find_ramge did not return 1 object")
            
            Property.mongodb.disconnect()
            
            #test GET queries
            response = self.client.get(reverse('api_feature'))
            response_dict = json.loads(response.content)
            self.assertEquals(len(response_dict['features']),
                              5,
                              "The retrieval of all features with mongodb did not work")
            
            response = self.client.get(reverse('api_feature') + "?some_prop=40")
            response_dict = json.loads(response.content)
            self.assertEquals(len(response_dict['features']),
                              2,
                              "The retrieval of some features with number as value did not work")
            
            response = self.client.get(reverse('api_feature') + "?some_prop=true")
            response_dict = json.loads(response.content)
            self.assertEquals(len(response_dict['features']),
                              1,
                              "The retrieval of some features with boolean as value did not work")
            
    
    def test_history(self):
        #features to save
        
        self.client.login(username='testuser', password='passwd')
        #save some values into the database
        geojson_feature = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature",
                "geometry": {"type":"Point",
                            "coordinates":[200, 200]},
                "properties": {"some_prop":"history_value"}},
                {"type": "Feature",
                "geometry": {"type":"Point",
                            "coordinates":[200, 200]},
                "properties": {"some_prop": 40}},
                {"type": "Feature",
                "geometry": {"type":"Point",
                            "coordinates":[200, 200]},
                "properties": {"some_prop": 40}},
                {"type": "Feature",
                 "geometry": {"type":"Point",
                            "coordinates":[200, 200]},
                 "properties": {"some_prop": True}},
                {"type": "Feature",
                 "geometry": {"type":"Point",
                            "coordinates":[200, 200]},
                 "properties": {"some_prop": 42}}
                ]
        }
        
        submit_time_gt = datetime.datetime.now()
        response = self.client.post(reverse('api_feature'),
                                json.dumps(geojson_feature),
                                content_type='application/json')
        
        response_dict = json.loads(response.content)
        submit_time_lt = datetime.datetime.now()
        
        time.sleep(1) #make sure it will be another second before update
        
        response_dict['features'][0]['properties']['good'] = 33
        
        submit2_time_gt = datetime.datetime.now()
        response = self.client.put(reverse('api_feature'),
                                json.dumps(response_dict),
                                content_type='application/json')
        
        submit2_time_lt = datetime.datetime.now()
        
        
        #start querying
        
        #should return all features just saved
        response = self.client.get(reverse('api_feature') + \
                                   "?expire_time__gt=%i-%i-%i-%i-%i-%i" % (submit_time_gt.year,
                                                                        submit_time_gt.month,
                                                                        submit_time_gt.day,
                                                                        submit_time_gt.hour,
                                                                        submit_time_gt.minute,
                                                                        submit_time_gt.second))
        
        response_dict = json.loads(response.content) 
        
        print response_dict
        print len(response_dict['features'])
        
        #should return only the new features
        response = self.client.get(reverse('api_feature') + \
                                   "?create_time__gt=%i-%i-%i-%i-%i-%i" % (submit_time_lt.year,
                                                                        submit_time_lt.month,
                                                                        submit_time_lt.day,
                                                                        submit_time_lt.hour,
                                                                        submit_time_lt.minute,
                                                                        submit_time_lt.second))
        
        response_dict = json.loads(response.content) 
        
        #print response_dict
        #print len(response_dict['features'])
        
        #should only return the new features
        response = self.client.get(reverse('api_feature') + \
                                   "?create_time__latest=true")
        
        response_dict = json.loads(response.content) 
        
        #print response_dict
        #print len(response_dict['features'])
        
        
        
        