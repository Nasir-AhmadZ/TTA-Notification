import aio_pika
from aio_pika import ExchangeType
import aiormq
import asyncio
import json
import os

from dotenv import load_dotenv

load_dotenv()

RABBITMQ_URL = os.getenv("RABBITMQ_URL")
QUEUE_NAME = os.getenv("QUEUE_NAME", "user_events_queue")


#currentUser = "691c8bf8d691e46d00068bf3" # default user id as string

if not RABBITMQ_URL:
    raise RuntimeError("RABBITMQ_URL is not set. Export it or add it to a .env file.")

async def _consume_once():
    global currentUser 
    currentUser =   "691c8bf8d691e46d00068bf3"
    print(f"Connecting to RabbitMQ at {RABBITMQ_URL}")
    connection = await aio_pika.connect(RABBITMQ_URL)

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        # Declare queue - login service publishes directly to this queue via default exchange
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)

        print(f"Waiting for messages on '{QUEUE_NAME}'...")

        try:
            async with queue.iterator() as q:
                async for message in q:
                    async with message.process():
                        try:
                            raw = message.body
                            if isinstance(raw, (bytes, bytearray)):
                                raw = raw.decode("utf-8")

                            payload = json.loads(raw)

                            user_id = None
                            event_type = None
                            data = None
                            if isinstance(payload, dict):
                                event_type = payload.get("event_type")
                                data = payload.get("data")

                                if event_type == "user_login": # on user login event, set currentUser
                                    user_id = payload.get("user_id")
                                    if not user_id and isinstance(data, dict):
                                        user_id = data.get("user_id")

                                    if user_id:
                                        currentUser = user_id
                                        print("Set currentUser=", currentUser)
                                
                                if event_type == "user_logout": # on user logout event, clear currentUser
                                    user_id = payload.get("user_id")
                                    if not user_id and isinstance(data, dict):
                                        user_id = data.get("user_id")

                                    if user_id:
                                        currentUser = "691c8bf8d691e46d00068bf3" #default user
                                        print("user logged out\nSet default currentUser=", currentUser)

                                if event_type == "user_deletion":  # on user deletion event, clear currentUser
                                    user_id = payload.get("user_id")
                                    if not user_id and isinstance(data, dict):
                                        user_id = data.get("user_id")

                                    if user_id:
                                        currentUser = "691c8bf8d691e46d00068bf3" #default user
                                        print("user deleted\nSet default currentUser=", currentUser)


                            print("Received event=", event_type, "data=", data)
                        except json.JSONDecodeError as e:
                            print("Invalid JSON in message body:", e)
                        except Exception as e:
                            print("Failed to process message:", e)
        except asyncio.CancelledError:
            print("Consumer cancelled")

async def consume():
    # Keep the consumer alive even if the connection drops; useful when running inside uvicorn
    while True:
        try:
            await _consume_once()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"Consumer loop error: {exc}; retrying in 5s")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(consume())
    except KeyboardInterrupt:
        print("Interrupted by user")
