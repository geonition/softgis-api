from django.db.models.query import QuerySet

class MongoQuerySet(QuerySet):
    """
    QuerySet to handle mongodatabase queries
    """
    
    ### Methods overloaded from QuerySet ###
    def __init__(self, model=None, query=None, using=None, mongo_collection=None):
        super(MongoQuerySet, self).__init__(model=model, query=query, using=using)
        self.mongo_collection = mongo_collection
        
    