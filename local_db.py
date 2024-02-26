'''
This module is for everything related to the MongoDb database
'''

import pymongo
import logger_setup
from datetime import datetime, timedelta
from time import mktime
from pymongo.mongo_client import MongoClient
from os import getenv
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
PWD = getenv('PWD')

# Set up logger for this file
local_db_logger = logger_setup.setup_logger(__name__, logger_setup.logging.DEBUG)

class Database:
    def __init__(self):
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

    def get_docs(self, col: str, start_time: int, end_time = int(mktime(datetime.now().timetuple()))):
        '''Returns entries within a specific time span. `start_time` is the unix date that the entries should come after. `end_time` is the unix date that entries should come before and its default value is today'''
        return self.db[col].find({"date": 
                                  {"$gte": start_time, "$lte": end_time }
                                })
    
    def get_unix_time(self, days_ago: int):
        '''Returns the unix time of `days_ago` days ago'''
        return int(mktime((datetime.now() - timedelta(days=days_ago)).timetuple()))
