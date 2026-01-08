import os
import sys
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId

#auto-detect if running under pytest
if "pytest" in sys.modules:
    import mongomock
    client = mongomock.MongoClient()
else:
    uri = os.getenv("MONGO_URI")
    client = MongoClient(uri, server_api=ServerApi('1'))

db = client.user_db
notifications_collection = db["notifications"]
