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
app = FastAPI(title="Notifications API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
currentUser = "691c8bf8d691e46d00068bf3"

RABBIT_URL = os.getenv("RABBIT_URL")
EXCHANGE_NAME = "notificiations_topic"
USE_EXCHANGE = os.getenv("USE_EXCHANGE", "true").lower() in ("1", "true", "yes")

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
    return [notification_helper(n) for n in notifications]

#get read notifications
@app.get("/notifications/read", response_model=list[GetNotificationsWithoutState], status_code=200)
def get_read_notifications():
    notifications = list(notifications_collection.find({"user_id": currentUser, "opened": True}))
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
def build_message_text(event_type: str, data: dict) -> str:
    name = (data or {}).get("name", "unknown")
    return {
        "entry.completed": f"Entry '{name}' completed",
        "entry.running": f"Entry '{name}' started",
        "entry.updated": f"Entry '{name}' updated",
        "project.created": f"Project '{name}' created",
    }.get(event_type, f"Event: {event_type}")


async def consume_notifications():
    try:
        print(f"Connecting to RabbitMQ: {RABBIT_URL}")
        connection = await aio_pika.connect_robust(RABBIT_URL)
        print("Connected to RabbitMQ successfully")
        
        async with connection:
            channel = await connection.channel()
            print(f"Declaring exchange: {EXCHANGE_NAME}")
            
            exchange = await channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC)
            queue = await channel.declare_queue("all_notifications", durable=True)
            
            print("Binding queue to exchange with routing_key='#'")
            await queue.bind(exchange, routing_key="#")
            print("Waiting for messages on all_notifications...")
            
            async with queue.iterator() as q:
                async for message in q:
                    async with message.process():
                        try:
                            raw = message.body.decode("utf-8")
                            payload = json.loads(raw)
                            print(f"Received message: {payload}")

                            event_type = payload.get("event_type")
                            user_id = payload.get("data", {}).get("currentUser")
                            data = payload.get("data")

                            if isinstance(data, dict) and "data" in data:
                                data = data["data"]

                            if not event_type or not user_id:
                                print(f"Skipping message missing event_type/currentUser: {payload}")
                                continue

                            message_text = build_message_text(event_type, data)

                            related_id = data.get("id") or data.get("_id")  # depending on your helper shape

                            notification = {
                                "user_id": user_id,
                                "message": message_text,
                                "related_id": related_id,
                                "event_type": event_type,
                                "opened": False,
                                "created_at": datetime.now(),
                            }

                            notifications_collection.insert_one(notification)
                            print(f"Inserted notification: {notification}")
                        except Exception as e:
                            print(f"Error processing message: {e}")
    except Exception as e:
        print(f"RabbitMQ connection error: {e}")
        await asyncio.sleep(5)
        # Retry connection
        asyncio.create_task(consume_notifications())


@app.on_event("startup")
async def startup_event():
    print("Starting RabbitMQ consumer...")
    asyncio.create_task(consume_notifications())


# python -m uvicorn app.main:app --reload
