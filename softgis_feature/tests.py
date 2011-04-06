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
        
        #delete non existing feature
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
                    "properties": {"some_prop": 39}},
                    {"type": "Feature",
                    "geometry": {"type":"Point",
                                "coordinates":[200, 200]},
                    "properties": {"some_prop": 40}},
                    {"type": "Feature",
                    "geometry": {"type":"Point",
                                "coordinates":[200, 200]},
                    "properties": {"some_prop": 41}},
                    {"type": "Feature",
                     "geometry": {"type":"Point",
                                "coordinates":[200, 200]},
                     "properties": {"some_prop": 42}},
                    {"type": "Feature",
                     "geometry": {"type":"Point",
                                "coordinates":[200, 200]},
                     "properties": {"some_prop": 43}}
                    ]
            }
            
            response = self.client.post(reverse('api_feature'),
                                     json.dumps(geojson_feature),
                                     content_type='application/json')
            
            #retrieve object out of scope some_prop__max=30
            response = self.client.get(reverse('api_feature') + "?some_prop__max=30")
            response_dict = json.loads(response.content)
            self.assertEquals(len(response_dict['features']),
                              0,
                              "The property query should have returned 0 features")
            
            #retrieve object out of scope some_prop__min=45
            response = self.client.get(reverse('api_feature') + "?some_prop__min=45")
            response_dict = json.loads(response.content)
            self.assertEquals(len(response_dict['features']),
                              0,
                              "The property query should have returned 0 features")
            
            #retrieve one object some_prop=40
            response = self.client.get(reverse('api_feature') + "?some_prop=40")
            response_dict = json.loads(response.content)
            self.assertEquals(len(response_dict['features']),
                              1,
                              "The property query should have returned 1 feature")
            
            #retrieve objects in scope some_prop__min=41&some_prop__max=45
            response = self.client.get(reverse('api_feature') + "?some_prop__min=41&some_prop__max=45")
            response_dict = json.loads(response.content)
            
            self.assertEquals(len(response_dict['features']),
                              3,
                              "The property query should have returned 3 features")
            
            
    
    def test_history(self):
        #features to save
        
        self.client.login(username='testuser', password='passwd')
        #save some values into the database
        geojson_feature = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature",
                "geometry": {"type":"Point",
                            "coordinates":[100, 200]},
                "properties": {"some_prop":"history_value",
                               "id": 1}},
                {"type": "Feature",
                "geometry": {"type":"Point",
                            "coordinates":[200, 200]},
                "properties": {"some_prop": 40,
                               "id": 2}},
                {"type": "Feature",
                "geometry": {"type":"Point",
                            "coordinates":[300, 200]},
                "properties": {"some_prop": 40,
                               "id": 3}},
                {"type": "Feature",
                 "geometry": {"type":"Point",
                            "coordinates":[400, 200]},
                 "properties": {"some_prop": True,
                               "id": 4}},
                {"type": "Feature",
                 "geometry": {"type":"Point",
                            "coordinates":[500, 200]},
                 "properties": {"some_prop": 42,
                               "id": 5}}
                ]
        }
        
        
        before_create = datetime.datetime.now()
        
        time.sleep(1) #wait a second to get smart queries
        
        response = self.client.post(reverse('api_feature'),
                                json.dumps(geojson_feature),
                                content_type='application/json')
        
        response_dict = json.loads(response.content)
        
        
        #wait a little bit to get difference
        time.sleep(1)
        after_create = datetime.datetime.now()
        time.sleep(1)
        response_dict['features'][0]['properties']['good'] = 33
        updated_feature_id = response_dict['features'][0]['id']
                
        response = self.client.put(reverse('api_feature'),
                                json.dumps(response_dict['features'][0]),
                                content_type='application/json')
        
        
        #delete one and check that the next delete does not affect it
        time.sleep(1)
        after_update = datetime.datetime.now()
        
        ids = []
        for feat in response_dict['features']:
            ids.append(feat['id'])
        
        deleted_feature_id = ids[0]
        response = self.client.delete(reverse('api_feature') + "?ids=[%s]" % deleted_feature_id)
        
        time.sleep(1)
        after_first_delete = datetime.datetime.now()
        
        #wait a little bit more
        time.sleep(1)
        
        response = self.client.delete(reverse('api_feature') + "?ids=%s" % json.dumps(ids))
        
        
        #wait a little bit more
        time.sleep(1)
        after_delete = datetime.datetime.now()
        
        
        
        #start querying
        
        #before first post there should be nothing
        response = self.client.get(reverse('api_feature') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (before_create.year,
                                                            before_create.month,
                                                            before_create.day,
                                                            before_create.hour,
                                                            before_create.minute,
                                                            before_create.second))
        
        response_dict = json.loads(response.content)
        self.assertTrue(len(response_dict['features']) == 0,
                        "Query with time before first post did not return an empty FeatureCollection")
        
        #query after first post
        response = self.client.get(reverse('api_feature') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (after_create.year,
                                                            after_create.month,
                                                            after_create.day,
                                                            after_create.hour,
                                                            after_create.minute,
                                                            after_create.second))
        
        response_dict = json.loads(response.content)
        amount_of_features = len(response_dict['features'])
        
        for feat in response_dict['features']:
            if feat['id'] == updated_feature_id:
                self.assertEquals(feat['properties']['id'],
                                   1,
                                  "The feature retrieves does not seem to have correct properties" + \
                                  " querying time before an update")
                self.assertEquals(feat['properties']['some_prop'],
                                  "history_value",
                                  "The feature retrieves does not seem to have correct properties" + \
                                  " querying time before an update")
        
        
        self.assertTrue(amount_of_features == 5,
                        "Query with time after first post did not return 5 " + \
                        "geojson Features. It returned %i" % amount_of_features)
        
        
        #query after update
        response = self.client.get(reverse('api_feature') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (after_update.year,
                                                            after_update.month,
                                                            after_update.day,
                                                            after_update.hour,
                                                            after_update.minute,
                                                            after_update.second))
        
        response_dict = json.loads(response.content)
        for feat in response_dict['features']:
            if feat['id'] == updated_feature_id:
                self.assertEquals(feat['properties']['good'],
                                  33,
                                  "The feature updated does not seem to have correct properties" + \
                                  " querying time after an update")
        
        amount_of_features = len(response_dict['features'])
        self.assertTrue(amount_of_features == 5,
                        "Query with time after update did not return 5 " + \
                        "geojson Features. It returned %i" % amount_of_features)
        
        
        #query after first delete
        response = self.client.get(reverse('api_feature') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (after_first_delete.year,
                                                            after_first_delete.month,
                                                            after_first_delete.day,
                                                            after_first_delete.hour,
                                                            after_first_delete.minute,
                                                            after_first_delete.second))
        
        
        response_dict = json.loads(response.content)
        
        
        #the deleted feature id should not be in the response
        for feature in response_dict['features']:
            self.assertNotEquals(feature['id'],
                                deleted_feature_id,
                                "Feature with id %i should have been deleted(expired) already" % deleted_feature_id)
        
        #query after deletion
        response = self.client.get(reverse('api_feature') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (after_delete.year,
                                                            after_delete.month,
                                                            after_delete.day,
                                                            after_delete.hour,
                                                            after_delete.minute,
                                                            after_delete.second))
        
        response_dict = json.loads(response.content)
        
        
        amount_of_features = len(response_dict['features'])
        self.assertTrue(amount_of_features == 0,
                        "Query with time after delete did not return 0 " + \
                        "geojson Features. It returned %i" % amount_of_features)
        
        
        #query with time__now=true should return the server time now features
        response = self.client.get(reverse('api_feature') + "?time__now=true")
        
        response_dict = json.loads(response.content)
        
        amount_of_features = len(response_dict['features'])
        self.assertTrue(amount_of_features == 0,
                        "Query with time__now=true did not return 0 " + \
                        "geojson Features. It returned %i" % amount_of_features)
        
        #query with time__now=false should return all
        response = self.client.get(reverse('api_feature') + \
                                   "?time__now=false")
        
        response_dict = json.loads(response.content)
        
        amount_of_features = len(response_dict['features'])
        self.assertTrue(amount_of_features == 6,
                        "Query with time__now=false did not return right amount of features  " + \
                        "geojson Features. It returned %i" % amount_of_features)
        
    def test_type_return(self):     
        self.client.login(username='testuser', password='passwd')
        #save some values into the database
        geojson_feature = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature",
                "geometry": {"type":"Point",
                            "coordinates":[100, 200]},
                "properties": {"float": 1.3,
                               "id": 1,
                               "boolean" : True,
                               "stringFloat" : "1.3",
                               "stringInt" : "1",
                               "stringBoolean" : "True"
                              }}
                ]
        }

        response = self.client.post(reverse('api_feature'),
                                json.dumps(geojson_feature),
                                content_type='application/json')
        
        response_dict = json.loads(response.content)
        id = response_dict['features'][0].get(u'id',-1)
        
        response = self.client.get(reverse('api_feature') + "?id=%i" % id)
        response_dict = json.loads(response.content)
        
        floatValue = response_dict["features"][0]["properties"]["float"]
        intValue = response_dict["features"][0]["properties"]["id"]
        booleanValue = response_dict["features"][0]["properties"]["boolean"]

        stringFloatValue = response_dict["features"][0]["properties"]["stringFloat"]
        stringIntValue = response_dict["features"][0]["properties"]["stringInt"]
        stringBooleanValue = response_dict["features"][0]["properties"]["stringBoolean"]


        self.assertEquals(floatValue, 1.3, "float value not retrieved correctly")
        self.assertEquals(intValue, 1, "int value not retrieved correctly")
        self.assertEquals(booleanValue, True, "boolean not retrieved correctly")

        self.assertEquals(stringFloatValue, "1.3", "string not retrieved correctly")
        self.assertEquals(stringIntValue, "1", "string not retrieved correctly")
        self.assertEquals(stringBooleanValue, "True", "string not retrieved correctly")
        
        """
        Further investigation needed for querying the features against same value either
        as a string or other type.
        EG: some_prop = 1.4 or some_prop = "1.4"
        How to difference between the two cases on the server?
        """
