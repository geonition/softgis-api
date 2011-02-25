from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

import datetime

import settings

import sys

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json


class StaticProfileValue(models.Model):
    """
    This model contains all the information of a user that
    is not dynamic. Meaning that it does not changes during
    a persons lifetime.
    """
    user = models.OneToOneField(User)
    #add here static profile values for each user
    allow_notifications = models.BooleanField(default=False)

    GENDER_CHOICES = (('M', 'Male'), ('F', 'Female'), )
    gender = models.CharField(blank=True,
                              null=True,
                              max_length = 1,
                              choices = GENDER_CHOICES)

    BIRTHYEAR_CHOICES = ()
    years = range(datetime.date.today().year - 100,
                  datetime.date.today().year - 5)
    for year in years:
        BIRTHYEAR_CHOICES = BIRTHYEAR_CHOICES + ((year, year),)
        
    birthyear = models.IntegerField(blank=True,
                                    null=True,
                                    choices = BIRTHYEAR_CHOICES)
    
    email_confirmed = models.BooleanField(default=False)
    

#signal handler for profile creation
def profile_handler(sender, instance, created, **kwargs):
    """
    This function makes sure that the extension profile values
    the StaticProfileValue is created for each user.

    it is connected to the post_save() signal of the user model
    """
    if created == True:
        try:
            associate_profile = StaticProfileValue(user=instance)
            associate_profile.save()
        except IntegrityError:
            django.db.connection.close()   
 
 
post_save.connect(profile_handler, sender=User)


   
class ProfileValue(models.Model):
    """
    additional possibly changing values to connect to
    a Persons profile
    """
    user = models.ForeignKey(User)
    json_string = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)
    expire_time = models.DateTimeField(null=True)
    
    def save(self, *args, **kwargs):
        """
        This function saves the new profile value and marks the old profile
        values as expired.
        """
        current_value = None
        current_value = \
            ProfileValue.objects.filter(user__exact = self.user)

        if(current_value.count() == 0):
            
            super(ProfileValue, self).save(*args, **kwargs)

            if(settings.USE_MONGODB):
                self.save_json_to_mongodb()
       
        else:
            current_value = current_value.latest('create_time')
            
            #update the values  
            current_dict = json.loads(current_value.json_string)
            new_dict = json.loads(self.json_string)
            current_dict.update(new_dict)
            self.json_string = json.dumps(current_dict)
            
            if(current_value.json_string == self.json_string):
                pass
            else:
                current_value.delete()

                super(ProfileValue, self).save(*args, **kwargs)
                
                if(settings.USE_MONGODB):
                    self.save_json_to_mongodb()

    def save_json_to_mongodb(self):
        """
        This function saves the JSON to the mongodb
        """
        insert_json = json.loads(self.json_string)
        insert_json['profile_id'] = int(self.id)
       
        con = Connection()
        
        db = con.softgis
        profiles = db.profiles
        obj_id = profiles.insert(insert_json)

        con.disconnect()

    def delete(self, *args, **kwargs):
        """
        This function sets the current profile value as
        expired
        """
        
        self.expire_time = datetime.datetime.today()
        super(ProfileValue, self).save(*args, **kwargs)
        
        return None

    def __unicode__(self):
        return self.json_string
        
    class Meta:
        get_latest_by = 'create_time'
        ordering = ['-create_time', 'user']
        permissions = (
            ("can_view_profiles", "can view profiles"),)
        unique_together = (("expire_time", "json_string", "user"),)
        


def get_user_profile(user):
    """
    returns a dictionary object of the given
    users profile
    """
    if not user.is_authenticated():
        return {}

    profile_dict = {}
    try:
        profile = ProfileValue.objects.filter(user__exact = user)\
                                      .latest('create_time')

        profile_dict = json.loads(profile.json_string)
    except ObjectDoesNotExist:
        pass

    try:
        profile_dict['allow_notifications'] = StaticProfileValue.objects\
                                                .get(user__exact = user)\
                                                .allow_notifications
        profile_dict['gender'] = StaticProfileValue.objects\
                                            .get(user__exact = user)\
                                            .gender
        profile_dict['email'] = StaticProfileValue.objects\
                                            .get(user__exact = user)\
                                            .user\
                                            .email
        profile_dict['birthyear'] = StaticProfileValue.objects\
                                            .get(user__exact = user)\
                                            .birthyear
    except ObjectDoesNotExist:
        pass
    
    return profile_dict

    
def get_profiles(limit_param, profile_queryset):
    """
    Returns a list of profiles that fits the limiting param and
    is in the given profile_queryset
    """
    if(profile_queryset == None):
        profile_queryset = ProfileValue.objects.all()

    profile_id_list = list(profile_queryset.values_list('id', flat=True))

    #open connection to mongodb
    con = None
    db = None
    profiles = None

    if(settings.USE_MONGODB):
        con = Connection()
        db = con.softgis
        profiles = db.profiles
    
    for key, value in limit_param:
        if(key == "user_id"):
            profile_queryset = profile_queryset.filter(user__exact = value)

        elif(key == "latest" and value == "true"):
            profile_queryset = profile_queryset.filter(expire_time__isnull=True)

        elif(settings.USE_MONGODB):

            try:
                value_name = key.split("__")[0]
                query_type = key.split("__")[1]
            except IndexError:
                query_type = None

            if(query_type == None):

                profile_ids = []
                for profile in profiles.find({key: value,
                                            "profile_id":
                                            {"$in": profile_id_list}}):
                                                
                    profile_ids.append(profile['profile_id'])

                profile_queryset = profile_queryset.filter(id__in = profile_ids)
                
            elif(query_type == "range"):
                min = value.split("-")[0]
                max = value.split("-")[1]

                profile_ids = []
                
                for profile in profiles.find({value_name: {"$lte": max,
                                                           "$gte": min},
                                            "profile_id": {"$in":
                                                           profile_id_list}}):
                                                               
                    profile_ids.append(profile['profile_id'])
                    
                profile_queryset = profile_queryset.filter(id__in = profile_ids)
                

    #close connection to mongodb
    if(settings.USE_MONGODB):
        con.disconnect()
    
    profile_list = []
    
    for profile in profile_queryset:
        profile_dict = json.loads(profile.json_string)
        profile_dict['allow_notifications'] = profile\
                                                .user\
                                                .staticprofilevalue\
                                                .allow_notifications
        profile_dict['gender'] = profile\
                                    .user\
                                    .staticprofilevalue\
                                    .gender
        profile_dict['birthyear'] = profile\
                                    .user\
                                    .staticprofilevalue\
                                    .birthyear
        profile_list.append(profile_dict)

    return profile_list        