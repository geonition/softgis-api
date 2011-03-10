from pymongo import Connection
from django.db.models import Manager

import settings

class MongoDBManager(Manager):
    """
    This manager includes functions
    to handle mongodb crud functionality.
    It combines the django model queries with
    information in mongodb.
    """
    
    #general connect and disconnect functions
    def connect(self,
                collection_name = 'collection'):
        """
        This function connects to MongoDB as set in
        the settings.py file.
        
        MONGODB_HOST = host to connect to
        MONGODB_PORT = port to use for connection
        MONGODB_DBNAME = name of database
        
        The collection name is model based and defined in the model.
        """
        #get connection values from settings
        database_host = getattr(settings, "MONGODB_HOST", 'localhost')
        database_port = getattr(settings, "MONGODB_PORT", 27017)
        database_name = getattr(settings, "MONGODB_DBNAME", 'softgis')

        self.connection = Connection(database_host, database_port)
        self.database = self.connection[database_name]
        self.collection = self.database[collection_name]
        
    def disconnect(self):
        """
        This function disconnects from the mongodb database.
        """
        self.connection.disconnect()
        
    #MongoDB insert functions and update functions
    def save(self, json_dict, identifier):
        """
        This function saves the jsondict and gives
        it the given identifier.
        """
        json_dict['_id'] = identifier
        self.collection.save(json_dict)
    
    #MongoDB remove functions
    def remove(self, identifier):
        """
        This functions removes the document with the given
        identifier from the collection.
        """
        self.collection.remove(identifier)
        
    #MongoDB query
    def find(self, spec=None):
        """
        This function returns a queryset including
        those objects that has the given key value pair.
        
        The spec is moved directly to mongodb for querying.
        """
        mdb_cursor = self.collection.find(spec)
        ids = []
        for json_obj in mdb_cursor:
            
            if(json_obj != None):
                ids.append(json_obj['_id'])
        
        return super(MongoDBManager, self).get_query_set().filter(id__in = ids)
        
    def find_range(self, key, min, max):
        """
        This functions returns a queryset with the objects that
        includes a key with a value between min and max.
        """
        return self.find({key: {"$gte": min, "$lte": max}})