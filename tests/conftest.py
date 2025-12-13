import pytest
from fastapi.testclient import TestClient
import mongomock
from app.main import app
from app import configurations

@pytest.fixture
def client():
    mock_client = mongomock.MongoClient()
    mock_db = mock_client.user_db
    
    configurations.db = mock_db
    configurations.notifications_collection = mock_db["notifications"]

    with TestClient(app) as c:
        yield c