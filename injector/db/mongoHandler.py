import pymongo
from abc import ABC
from injector.config import Config


class Mongo(ABC):
    def __init__(self, db_name, collection_name):
        self.client = pymongo.MongoClient(f"mongodb://{Config.getMongoHost()}:{Config.getMongoPort()}/")
        self.db_name = db_name
        self.collection_name = collection_name
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]

    def insert(self, data):
        self.collection.insert_one(data)

    def insert_many(self, data):
        self.collection.insert_many(data)
