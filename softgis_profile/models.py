from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db import IntegrityError
from manager import MongoDBManager

import django
import datetime
import settings
import sys

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json

#this can be used instead of writing getattr everywhere
USE_MONGODB = getattr(settings, "USE_MONGODB", False)

class Profile(models.Model):
    """
    additional possibly changing values to connect to
    a Persons profile
    """
    user = models.ForeignKey(User)
    json_string = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)
    expire_time = models.DateTimeField(null=True)
    
    objects = models.Manager()
    
    if USE_MONGODB:
        mongodb_collection_name = 'profiles'
        mongodb = MongoDBManager(collection_name = mongodb_collection_name) #manager for querying json

    
    def save(self, *args, **kwargs):    
        #save this new property
        super(Profile, self).save(*args, **kwargs)
        
        self.save_json_to_mongodb()
        
            
    def update(self, json_string, *args, **kwargs):
        
        if self.json_string != json_string:
            
            #set old feature as expired
            self.expire_time = datetime.datetime.today()
            super(Profile, self).save(*args, **kwargs)
            
            #save the new property
            new_profile = Profile(user = self.user,
                                json_string = json_string)
            new_profile.save()
            
            return new_profile
        
        return self

        
    def delete(self, *args, **kwargs):
        self.expire_time = datetime.datetime.today()

        super(Profile, self).save(*args, **kwargs)
        
        return None
    
    
    def save_json_to_mongodb(self):
        """
        This function saves the JSON to mongodb
        """
        #do nothing if USE_MONGODB False
        if USE_MONGODB:
            insert_json = json.loads(self.json_string)
            Profile.mongodb.save(insert_json, self.id)
            
    def json(self):
        json_dict = json.loads(self.json_string)
        json_dict['user_id'] = self.user.id
        json_dict['create_time'] = "%s-%s-%s-%s-%s-%s" % (self.create_time.year,
                                                       self.create_time.month,
                                                       self.create_time.day,
                                                       self.create_time.hour,
                                                       self.create_time.minute,
                                                       self.create_time.second)
        if self.expire_time == None:
            json_dict['expire_time'] = None
        else:
            json_dict['expire_time'] = "%s-%s-%s-%s-%s-%s" % (self.expire_time.year,
                                                           self.expire_time.month,
                                                           self.expire_time.day,
                                                           self.expire_time.hour,
                                                           self.expire_time.minute,
                                                           self.expire_time.second)
        
        return json_dict
        
    def __unicode__(self):
        return self.json_string
        
    class Meta:
        get_latest_by = 'create_time'
        permissions = (
            ("can_view_profiles", "can view profiles"),)
        unique_together = (("expire_time", "json_string", "user"),)
        