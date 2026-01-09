from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from bson import ObjectId
import os
import aio_pika
import json
import asyncio
from dotenv import load_dotenv
load_dotenv()
from .models import notification_helper
from .schemas import GetNotificationsWithoutState, Notification, NotificationUpdate
from .configurations import db, notifications_collection
from . import consumer
from . import consumerNotif
from contextlib import asynccontextmanager

app = FastAPI(title="Notifications API")

#******************************RabbitMQ stuff******************************************
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background consumers on app startup and cancel them on shutdown."""
    tasks = []

    try:
        print("Starting background RabbitMQ consumers")
        # user events consumer (sets user_id)
        user_task = asyncio.create_task(consumer.consume())
        tasks.append(user_task)

        # notifications consumer (inserts into notifications_collection)
        notif_task = asyncio.create_task(consumerNotif.consume())
        tasks.append(notif_task)

        app.state.consumer_tasks = tasks
    except Exception as e:
        print(f"ERROR: Failed to start consumer tasks: {e}")

    try:
        yield
    finally:
        for t in getattr(app.state, "consumer_tasks", []):
            try:
                t.cancel()
            except Exception:
                pass
        # Await cancellation
        for t in getattr(app.state, "consumer_tasks", []):
            try:
                await t
            except asyncio.CancelledError:
                pass

app = FastAPI(title="Notifications API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
#currentUser = "691c8bf8d691e46d00068bf3"

RABBIT_URL = os.getenv("RABBIT_URL")
EXCHANGE_NAME = "notificiations_topic"
USE_EXCHANGE = os.getenv("USE_EXCHANGE", "true").lower() in ("1", "true", "yes")

if not RABBIT_URL:
    raise RuntimeError("RABBIT_URL is not set. Export it (e.g. export RABBIT_URL='amqps://user:pass@host/vhost') or load your .env.")



#******************************Notification endpoints**********************************
#get all notifications
@app.get("/notifications/{user_id}", response_model=list[GetNotificationsWithoutState], status_code=200)
def get_notifications():
    notifications = list(notifications_collection.find({"user_id": user_id}))
    if not notifications:
        raise HTTPException(status_code=404, detail="No notifications found")
    return [notification_helper(n) for n in notifications]


# Get unread notifications
@app.get("/notifications/unread/{user_id}", response_model=list[GetNotificationsWithoutState], status_code=200)
def get_unread_notifications():
    notifications = list(notifications_collection.find({"user_id": user_id, "opened": False}))
    return [notification_helper(n) for n in notifications]

#get read notifications
@app.get("/notifications/read/{user_id}", response_model=list[GetNotificationsWithoutState], status_code=200)
def get_read_notifications():
    notifications = list(notifications_collection.find({"user_id": user_id, "opened": True}))
    if not notifications:
        raise HTTPException(status_code=404, detail="No read notifications found")
    return [notification_helper(n) for n in notifications]


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

# delete all notifications belongin to a user
@app.delete("/notifications/{user_id}", status_code=200)
def delete_notifications():
    notifications_collection.delete_many({"user_id": user_id})
    return {"message": "Notifications deleted"}

#delete notifications by related_id
@app.delete("/notifications/related/{related_id}")
def delete_notifications_by_related_Id(related_id: str):
    notifications_collection.delete_many({"related_id": related_id})
    return {"message": "Notifications deleted"}

# python -m uvicorn app.main:app --reload
