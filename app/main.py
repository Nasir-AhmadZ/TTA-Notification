from fastapi import FastAPI, HTTPException
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
app = FastAPI(title="Notifications API")

currentUser = "691c8bf8d691e46d00068bf3"

RABBIT_URL = os.getenv("RABBIT_URL")
EXCHANGE_NAME = "notificiations_topic"
if not RABBIT_URL:
    raise RuntimeError("RABBIT_URL is not set. Export it (e.g. export RABBIT_URL='amqps://user:pass@host/vhost') or load your .env.")



#******************************Notification endpoints**********************************
#get all notifications
@app.get("/notifications", response_model=list[GetNotificationsWithoutState], status_code=200)
def get_notifications():
    notifications = list(notifications_collection.find({"user_id": currentUser}))
    if not notifications:
        raise HTTPException(status_code=404, detail="No notifications found")
    return [notification_helper(n) for n in notifications]


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

# delete all notifications belongin to a user
@app.delete("/notifications", status_code=200)
def delete_notifications():
    notifications_collection.delete_many({"user_id": currentUser})
    return {"message": "Notifications deleted"}

#delete notifications by related_id
@app.delete("/notifications/related/{related_id}")
def delete_notifications_by_related_Id(related_id: str):
    notifications_collection.delete_many({"related_id": related_id})
    return {"message": "Notifications deleted"}

##************************Rabbitmq messaging********************************



async def consume_notifications():
    connection = await aio_pika.connect_robust(RABBIT_URL)
    channel = await connection.channel()
    
    exchange = await channel.declare_exchange("notificiations_topic", aio_pika.ExchangeType.TOPIC)
    queue = await channel.declare_queue("entry_notifications", durable=True)
    await queue.bind(exchange, routing_key="entry.completed")
    
    print("waiting for messages on entry_notifications ...")
    
    async with queue.iterator() as q:
        async for message in q:
            async with message.process():
                body_bytes = bytes(message.body)
                data = json.loads(body_bytes.decode("utf-8"))
                
                notification = {
                    "user_id": data["user_id"],
                    "message": f"Entry '{data['data']['name']}' completed",
                    "related_id": data["data"]["id"],
                    "opened": False,
                    "created_at": datetime.now()
                }
                notifications_collection.insert_one(notification)

@app.on_event("startup")
async def startup_event():
    import asyncio
    asyncio.create_task(consume_notifications())

# python -m uvicorn app.main:app --reload
