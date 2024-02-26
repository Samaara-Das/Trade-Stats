'''
this connects to either a remote/local database (depending on what is chosen).
this can add documents to the collection's database and delete all of them.
this also retrieves the latest document from the collection
'''

import pymongo
import logger_setup
from pymongo.mongo_client import MongoClient

# Set up logger for this file
local_db_logger = logger_setup.setup_logger(__name__, logger_setup.logging.DEBUG)

PWD = 'kdgzKyjYr8WA6Vkm'

class Database:
    def __init__(self, col, delete=False):
        # for a connection to local database (the connection string was from the mongo shell when i typed "mongosh"):
        # self.client = MongoClient("mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+1.10.3")

        # for a connection to remote database:
        self.client = MongoClient(f"mongodb+srv://sammy:{PWD}@cluster1.565lfln.mongodb.net/?retryWrites=true&w=majority")
        
        try:
            self.client.admin.command('ping')
            local_db_logger.info("You successfully connected to MongoDB!") # Send a ping to confirm a successful connection
        except Exception as e:
            local_db_logger.exception(f'Failed to connect to MongoDB database. Error:')
            return
        
        self.db = self.client["tradingview-to-everywhere"]

        if delete:
            self.delete_all(col)
            local_db_logger.info("Successfully deleted all documents")

    def add_doc(self, doc: dict, col: str):
        '''Adds `doc` to a specific collection'''
        try:
            self.db[col].insert_one(doc)
            local_db_logger.info(f"Successfully sent a doc to {col} collection!")
            return True
        except Exception as e:
            local_db_logger.exception(f'Failed to add document to MongoDB\'s {col} collection. Error:')
            return False

    def get_latest_doc(self, col: str):
        docs = self.db[col].find_one(sort=[("_id", pymongo.DESCENDING)])
        return docs

    def delete_all(self, col: str):
        self.db[col].delete_many({}) 

    def delete_some(self, count: int, col: str):
        '''This will keep the latest `count` documents and deletes the rest of them. It will also log how many docs got deleted'''
        
        latest_100_ids = [x['_id'] for x in self.db[col].find().sort('_id', pymongo.DESCENDING).limit(count)] # Get the IDs of the latest 100 documents
        result = self.db[col].delete_many({'_id': {'$nin': latest_100_ids}}) # Delete all documents that are not in the latest 100
        local_db_logger.info(f"Deleted {result.deleted_count} documents from {col} collection.")


