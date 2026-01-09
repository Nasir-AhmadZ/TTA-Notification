import pytest
from fastapi.testclient import TestClient
import mongomock
from app.main import app
from app import configurations

@pytest.fixture
def client():
    # The configurations.py already sets up mongomock when pytest is running
    # Just clear the collection before each test
    configurations.notifications_collection.delete_many({})
    
    with TestClient(app) as c:
        yield c
        # clear the collection after the test
        configurations.notifications_collection.delete_many({})