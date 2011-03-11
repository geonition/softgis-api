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
            
            
            #TODO write tests to test the REST
            
    
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
        
        
        submit_before = datetime.datetime.now()
        
        time.sleep(1) #wait a second to get smart queries
        
        response = self.client.post(reverse('api_feature'),
                                json.dumps(geojson_feature),
                                content_type='application/json')
        
        response_dict = json.loads(response.content)
        
        #wait a little bit to get difference
        time.sleep(1)
        submit_after = datetime.datetime.now()
        
        response_dict['features'][0]['properties']['good'] = 33
        
        submit2_before = datetime.datetime.now()
        time.sleep(1) # wait to get smart query
        
        response = self.client.put(reverse('api_feature'),
                                json.dumps(response_dict),
                                content_type='application/json')
        
        
        #wait a little bit more
        time.sleep(1)
        submit2_after = datetime.datetime.now()
        
        submit3_before = datetime.datetime.now()
        time.sleep(1) # wait to get smart query
        ids = []
        for feat in response_dict['features']:
            ids.append(feat['id'])
        
        response = self.client.delete(reverse('api_feature') + "?ids=%s" % json.dumps(ids))
        
        
        #wait a little bit more
        time.sleep(1)
        submit3_after = datetime.datetime.now()
        
        
        
        #start querying
        
        #print "create_time__gt query with"
        #print submit_time_gt
        
        #should return all features just saved
        response = self.client.get(reverse('api_feature') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (submit_before.year,
                                                            submit_before.month,
                                                            submit_before.day,
                                                            submit_before.hour,
                                                            submit_before.minute,
                                                            submit_before.second))
        
        response_dict = json.loads(response.content) 
        
        #print response_dict
        print "should return 0"
        print len(response_dict['features'])
        
        
        
        #print "create_time__lt query with"
        #print submit_time_lt
        
        #should return only the new features
        response = self.client.get(reverse('api_feature') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (submit_after.year,
                                                                submit_after.month,
                                                                submit_after.day,
                                                                submit_after.hour,
                                                                submit_after.minute,
                                                                submit_after.second))
        
        response_dict = json.loads(response.content) 
        
        #print response_dict
        print "should return 5"
        print len(response_dict['features'])
        
        #should return only the new features
        response = self.client.get(reverse('api_feature') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (submit2_before.year,
                                                                submit2_before.month,
                                                                submit2_before.day,
                                                                submit2_before.hour,
                                                                submit2_before.minute,
                                                                submit2_before.second))
        
        response_dict = json.loads(response.content) 
        
        #print response_dict
        print "should return 5"
        print len(response_dict['features'])
        
        #should return only the new features
        response = self.client.get(reverse('api_feature') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (submit2_after.year,
                                                                submit2_after.month,
                                                                submit2_after.day,
                                                                submit2_after.hour,
                                                                submit2_after.minute,
                                                                submit2_after.second))
        
        response_dict = json.loads(response.content) 
        
        #print response_dict
        print "should return 5"
        print len(response_dict['features'])
        
        #should return only the new features
        response = self.client.get(reverse('api_feature') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (submit3_after.year,
                                                                submit3_after.month,
                                                                submit3_after.day,
                                                                submit3_after.hour,
                                                                submit3_after.minute,
                                                                submit3_after.second))
        
        response_dict = json.loads(response.content) 
        
        #print response_dict
        print "should return 5"
        print len(response_dict['features'])
        
        #should return only the new features
        response = self.client.get(reverse('api_feature') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (submit3_after.year,
                                                                submit3_after.month,
                                                                submit3_after.day,
                                                                submit3_after.hour,
                                                                submit3_after.minute,
                                                                submit3_after.second))
        
        response_dict = json.loads(response.content) 
        
        #print response_dict
        print "should return 0"
        print len(response_dict['features'])
        
        
        
        