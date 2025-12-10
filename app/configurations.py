
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = os.getenv("MONGO_URI")

# create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

db = client.notifications
notifications_collection = db["notifications"]

