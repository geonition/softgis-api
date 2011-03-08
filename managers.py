from django.db import models
from pymongo import Connection


class MongoDBManager(models.Manager):
    """
    This manager helps with mongodb get
    queries.
    """
    
    def __init__(self):
        pass
    
    #MongoDB functions
    def save(self, json):
        pass
    
    def get_exists(self, key):
        pass
    
    def get_gt(self, key, value):
        pass
    
    def get_gte(self, key, value):
        pass
    
    def get_lt(self, key, value):
        pass
    
    def get_lte(self, key, value):
        pass
    
    def get_in(self, key, value_list):
        pass
        
        
