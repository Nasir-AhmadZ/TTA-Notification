import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from datetime import datetime
from app.main import app
import mongomock
from app import configurations

example_notification = {
    "user_id": "691c8bf8d691e46d00068bf3",
    "message": "Test notification",
    "related_id": "691c8bf8d691e46d00068bf4",
    "event_type": "entry.completed",
    "opened": False,
    "created_at": datetime.now()
}

def test_get_notifications_empty(client):
    response = client.get("/notifications")
    assert response.status_code == 404

# def test_get_notifications_with_data(client):
#     from app.configurations import notifications_collection
#     notifications_collection.insert_one(example_notification)
    
#     response = client.get("/notifications")
#     assert response.status_code == 200
#     assert len(response.json()) == 1

# def test_get_unread_notifications(client):
#     from app.configurations import notifications_collection
#     notifications_collection.insert_one(example_notification)
    
#     response = client.get("/notifications/unread")
#     assert response.status_code == 200

def test_get_read_notifications_empty(client):
    from app.configurations import notifications_collection
    notifications_collection.insert_one(example_notification)
    
    response = client.get("/notifications/read")
    assert response.status_code == 404

# def test_update_notification_status(client):
#     from app.configurations import notifications_collection
#     result = notifications_collection.insert_one(example_notification)
#     notification_id = str(result.inserted_id)
    
#     response = client.patch(f"/notifications/{notification_id}", json={"opened": True})
#     assert response.status_code == 200

def test_update_nonexistent_notification(client):
    fake_id = str(ObjectId())
    response = client.patch(f"/notifications/{fake_id}", json={"opened": True})
    assert response.status_code == 404

def test_delete_notification(client):
    from app.configurations import notifications_collection
    result = notifications_collection.insert_one(example_notification)
    notification_id = str(result.inserted_id)
    
    response = client.delete(f"/notifications/{notification_id}")
    assert response.status_code == 200

def test_delete_all_notifications(client):
    from app.configurations import notifications_collection
    notifications_collection.insert_one(example_notification)
    
    response = client.delete("/notifications")
    assert response.status_code == 200

def test_delete_notifications_by_related_id(client):
    from app.configurations import notifications_collection
    notifications_collection.insert_one(example_notification)
    
    response = client.delete(f"/notifications/related/{example_notification['related_id']}")
    assert response.status_code == 200