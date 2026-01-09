import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from datetime import datetime
from app.main import app
import mongomock
from app import configurations
from app.models import notification_helper
from app.schemas import NotificationUpdate

example_notification = {
    "user_id": "691c8bf8d691e46d00068bf3",
    "message": "Test notification",
    "related_id": "691c8bf8d691e46d00068bf4",
    "event_type": "entry.completed",
    "opened": False,
    "created_at": datetime.now()
}

# ==================== GET NOTIFICATIONS ====================
def test_get_notifications_empty(client):
    """Test getting notifications for non-existent user"""
    response = client.get("/notifications/691c8bf8d691e46d00068bf3")
    assert response.status_code == 404
    assert "No notifications found" in response.json()["detail"]

def test_get_notifications_with_data(client):
    """Test getting notifications for user with notifications"""
    from app.configurations import notifications_collection
    notifications_collection.insert_one(example_notification)
    
    response = client.get(f"/notifications/{example_notification['user_id']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["message"] == "Test notification"

def test_get_notifications_multiple(client):
    """Test getting multiple notifications for a user"""
    from app.configurations import notifications_collection
    notif1 = {
        "user_id": "user_multi_test",
        "message": "First notification",
        "related_id": "691c8bf8d691e46d00068bf4",
        "event_type": "entry.completed",
        "opened": False,
        "created_at": datetime.now()
    }
    notif2 = {
        "user_id": "user_multi_test",
        "message": "Second notification",
        "related_id": "691c8bf8d691e46d00068bf5",
        "event_type": "entry.completed",
        "opened": False,
        "created_at": datetime.now()
    }
    
    notifications_collection.insert_many([notif1, notif2])
    
    response = client.get("/notifications/user_multi_test")
    assert response.status_code == 200
    assert len(response.json()) == 2

# ==================== GET UNREAD NOTIFICATIONS ====================
def test_get_unread_notifications_none(client):
    """Test getting unread notifications when there are none"""
    from app.configurations import notifications_collection
    notif = example_notification.copy()
    notif["opened"] = True
    notifications_collection.insert_one(notif)
    
    response = client.get(f"/notifications/unread/{example_notification['user_id']}")
    assert response.status_code == 200
    assert len(response.json()) == 0

def test_get_unread_notifications_exists(client):
    """Test getting unread notifications"""
    from app.configurations import notifications_collection
    notif = {
        "user_id": "user_unread",
        "message": "Unread notification",
        "related_id": "691c8bf8d691e46d00068bf4",
        "event_type": "entry.completed",
        "opened": False,
        "created_at": datetime.now()
    }
    notifications_collection.insert_one(notif)
    
    response = client.get("/notifications/unread/user_unread")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["message"] == "Unread notification"

def test_get_unread_notifications_mixed(client):
    """Test getting unread notifications when there are both read and unread"""
    from app.configurations import notifications_collection
    notif1 = {
        "user_id": "user_mixed",
        "message": "Unread notification",
        "related_id": "691c8bf8d691e46d00068bf4",
        "event_type": "entry.completed",
        "opened": False,
        "created_at": datetime.now()
    }
    notif2 = {
        "user_id": "user_mixed",
        "message": "Read notification",
        "related_id": "691c8bf8d691e46d00068bf5",
        "event_type": "entry.completed",
        "opened": True,
        "created_at": datetime.now()
    }
    
    notifications_collection.insert_many([notif1, notif2])
    
    response = client.get("/notifications/unread/user_mixed")
    assert response.status_code == 200
    assert len(response.json()) == 1

# ==================== GET READ NOTIFICATIONS ====================
def test_get_read_notifications_empty(client):
    """Test getting read notifications when there are none"""
    from app.configurations import notifications_collection
    notifications_collection.insert_one(example_notification)
    
    response = client.get(f"/notifications/read/{example_notification['user_id']}")
    assert response.status_code == 404
    assert "No read notifications found" in response.json()["detail"]

def test_get_read_notifications_exists(client):
    """Test getting read notifications"""
    from app.configurations import notifications_collection
    notif = {
        "user_id": "user_read",
        "message": "Read notification",
        "related_id": "691c8bf8d691e46d00068bf4",
        "event_type": "entry.completed",
        "opened": True,
        "created_at": datetime.now()
    }
    notifications_collection.insert_one(notif)
    
    response = client.get("/notifications/read/user_read")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

def test_get_read_notifications_mixed(client):
    """Test getting read notifications when there are both read and unread"""
    from app.configurations import notifications_collection
    notif1 = {
        "user_id": "user_mixed_read",
        "message": "Unread notification",
        "related_id": "691c8bf8d691e46d00068bf4",
        "event_type": "entry.completed",
        "opened": False,
        "created_at": datetime.now()
    }
    notif2 = {
        "user_id": "user_mixed_read",
        "message": "Read notification",
        "related_id": "691c8bf8d691e46d00068bf5",
        "event_type": "entry.completed",
        "opened": True,
        "created_at": datetime.now()
    }
    
    notifications_collection.insert_many([notif1, notif2])
    
    response = client.get("/notifications/read/user_mixed_read")
    assert response.status_code == 200
    assert len(response.json()) == 1

# ==================== UPDATE NOTIFICATIONS ====================
def test_update_notification_status(client):
    """Test updating notification status"""
    from app.configurations import notifications_collection
    notif = {
        "user_id": "user_update",
        "message": "Update test",
        "related_id": "691c8bf8d691e46d00068bf4",
        "event_type": "entry.completed",
        "opened": False,
        "created_at": datetime.now()
    }
    result = notifications_collection.insert_one(notif)
    notification_id = str(result.inserted_id)
    
    response = client.patch(f"/notifications/{notification_id}", json={"opened": True})
    assert response.status_code == 200
    assert response.json()["message"] == "Notification status updated"
    
    # Verify it was updated
    updated = notifications_collection.find_one({"_id": ObjectId(notification_id)})
    assert updated["opened"] is True

def test_update_notification_to_false(client):
    """Test updating notification status back to unread"""
    from app.configurations import notifications_collection
    notif = {
        "user_id": "user_update_false",
        "message": "Update to false test",
        "related_id": "691c8bf8d691e46d00068bf4",
        "event_type": "entry.completed",
        "opened": True,
        "created_at": datetime.now()
    }
    result = notifications_collection.insert_one(notif)
    notification_id = str(result.inserted_id)
    
    response = client.patch(f"/notifications/{notification_id}", json={"opened": False})
    assert response.status_code == 200
    
    updated = notifications_collection.find_one({"_id": ObjectId(notification_id)})
    assert updated["opened"] is False

def test_update_nonexistent_notification(client):
    """Test updating non-existent notification"""
    fake_id = str(ObjectId())
    response = client.patch(f"/notifications/{fake_id}", json={"opened": True})
    assert response.status_code == 404
    assert "Notification not found" in response.json()["detail"]

def test_update_notification_invalid_id(client):
    """Test updating with invalid notification ID"""
    response = client.patch("/notifications/invalid_id", json={"opened": True})
    assert response.status_code == 400
    assert "Invalid notification id" in response.json()["detail"]

# ==================== DELETE NOTIFICATIONS ====================
def test_delete_notification_by_id(client):
    """Test deleting notification by its ID"""
    from app.configurations import notifications_collection
    notif = {
        "user_id": "user_delete",
        "message": "Delete test",
        "related_id": "691c8bf8d691e46d00068bf4",
        "event_type": "entry.completed",
        "opened": False,
        "created_at": datetime.now()
    }
    result = notifications_collection.insert_one(notif)
    notification_id = str(result.inserted_id)
    
    response = client.delete(f"/notifications/{notification_id}")
    assert response.status_code == 200
    # Verify it was deleted
    deleted = notifications_collection.find_one({"_id": ObjectId(notification_id)})
    assert deleted is None

def test_delete_all_notifications_by_user(client):
    """Test deleting all notifications for a user"""
    from app.configurations import notifications_collection
    user_id = "691c8bf8d691e46d00068bf3"
    notif1 = {
        "user_id": user_id,
        "message": "Test notification",
        "related_id": "691c8bf8d691e46d00068bf4",
        "event_type": "entry.completed",
        "opened": False,
        "created_at": datetime.now()
    }
    notif2 = {
        "user_id": user_id,
        "message": "Second",
        "related_id": "691c8bf8d691e46d00068bf5",
        "event_type": "entry.completed",
        "opened": False,
        "created_at": datetime.now()
    }
    
    notifications_collection.insert_many([notif1, notif2])
    
    response = client.delete(f"/notifications/{user_id}")
    assert response.status_code == 200
    assert "Notifications deleted (2)" in response.json()["message"]
    
    # Verify all deleted
    remaining = list(notifications_collection.find({"user_id": user_id}))
    assert len(remaining) == 0

def test_delete_notifications_by_related_id(client):
    """Test deleting notifications by related ID"""
    from app.configurations import notifications_collection
    related_id = "691c8bf8d691e46d00068bf4"
    notif1 = {
        "user_id": "user1",
        "message": "Test notification",
        "related_id": related_id,
        "event_type": "entry.completed",
        "opened": False,
        "created_at": datetime.now()
    }
    notif2 = {
        "user_id": "user2",
        "message": "Another",
        "related_id": related_id,
        "event_type": "entry.completed",
        "opened": False,
        "created_at": datetime.now()
    }
    
    notifications_collection.insert_many([notif1, notif2])
    
    response = client.delete(f"/notifications/related/{related_id}")
    assert response.status_code == 200
    
    # Verify those with related_id were deleted
    remaining = list(notifications_collection.find({"related_id": related_id}))
    assert len(remaining) == 0

def test_delete_nonexistent_notification(client):
    """Test deleting non-existent notification by ID"""
    fake_id = str(ObjectId())
    response = client.delete(f"/notifications/{fake_id}")
    assert response.status_code == 200
    assert "Notifications deleted (0)" in response.json()["message"]

# ==================== HELPER FUNCTION TESTS ====================
def test_notification_helper():
    """Test notification_helper function"""
    test_doc = {
        "_id": ObjectId(),
        "message": "Test message",
        "related_id": "some_id",
        "created_at": datetime.now()
    }
    
    result = notification_helper(test_doc)
    
    assert "id" in result
    assert result["message"] == "Test message"
    assert result["related_id"] == "some_id"
    assert "timestamp" in result
