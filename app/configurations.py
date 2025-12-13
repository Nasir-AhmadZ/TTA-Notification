
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId

uri = os.getenv("MONGO_URI")

# create a new client and connect to the server
if uri:
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client.notifications
    notifications_collection = db["notifications"]
else:
    client = None
    db = None
    notifications_collection = None

