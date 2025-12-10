from fastapi import FastAPI, HTTPException
from datetime import datetime
from bson import ObjectId

from .schemas import GetNotificationsWithoutState, Notification, NotificationUpdate
from .models import entry_helper, project_helper
from .configurations import db, notifications_collection
app = FastAPI(title="Notifications API")

currentUser = "691c8bf8d691e46d00068bf3"

#******************************Notification endpoints**********************************
#get all notifications
@app.get("/notifications", response_model=list[GetNotificationsWithoutState], status_code=200)
def get_notifications():
    notifications = list(notifications_collection.find({"user_id": currentUser}))
    if not notifications:
        raise HTTPException(status_code=404, detail="No notifications found")
    return notifications

# Get unread notifications
@app.get("/notifications/unread", response_model=list[GetNotificationsWithoutState], status_code=200)
def get_unread_notifications():
    notifications = list(notifications_collection.find({"user_id": currentUser, "opened": False}))
    if not notifications:
        raise HTTPException(status_code=404, detail="No notifications found")
    return notifications

#get read notifications
@app.get("/notifications/read", response_model=list[GetNotificationsWithoutState], status_code=200)
def get_read_notifications():
    notifications = list(notifications_collection.find({"user_id": currentUser, "opened": True}))
    if not notifications:
        raise HTTPException(status_code=404, detail="No notifications found")
    return notifications


@app.patch("/notifications/{notification_id}", response_model=dict, status_code=200)
def update_notification_status(notification_id: str, update: NotificationUpdate):
    notification = notifications_collection.find_one({"_id": ObjectId(notification_id)})
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notifications_collection.update_one(
        {"_id": ObjectId(notification_id)},
        {"$set": {"opened": update.opened}}
    )
    
    return {"message": "Notification status updated"}

#delete notification by id
@app.delete("/notifications/{notification_id}", status_code=200)
def delete_notification(notification_id: str):
    notifications_collection.delete_one({"_id": ObjectId(notification_id)})
    return {"message": "Notification deleted"}


# python -m uvicorn app.main:app --reload
