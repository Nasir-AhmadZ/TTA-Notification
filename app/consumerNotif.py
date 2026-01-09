import aio_pika
from aio_pika import ExchangeType
import asyncio
import json
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

RABBIT_URL = os.getenv("RABBIT_URL")
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "notificiations_topic")
QUEUE_NAME = os.getenv("NOTIFICATIONS_QUEUE", "all_notifications")

from .configurations import notifications_collection

if not RABBIT_URL:
    raise RuntimeError("RABBIT_URL is not set. Export it or add it to a .env file.")


def build_message_text(event_type: str, data: dict) -> str:
    name = (data or {}).get("name", "unknown")
    return {
        "entry.completed": f"Entry '{name}' completed",
        "entry.running": f"Entry '{name}' started",
        "entry.updated": f"Entry '{name}' updated",
        "project.created": f"Project '{name}' created",
    }.get(event_type, f"Event: {event_type}")


async def _consume_once():
    print(f"Connecting to RabbitMQ at {RABBIT_URL}")
    connection = await aio_pika.connect_robust(RABBIT_URL)

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        # Declare exchange and queue, bind with wildcard
        # NOTE: the existing exchange on the broker is non-durable, so declare
        # with durable=False to avoid PRECONDITION_FAILED when the exchange
        # already exists with differing attributes.
        exchange = await channel.declare_exchange(EXCHANGE_NAME, ExchangeType.TOPIC, durable=False)
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        await queue.bind(exchange, routing_key="#")

        print(f"Waiting for messages on '{QUEUE_NAME}' bound to exchange '{EXCHANGE_NAME}'...")

        try:
            async with queue.iterator() as q:
                async for message in q:
                    async with message.process():
                        try:
                            raw = message.body
                            if isinstance(raw, (bytes, bytearray)):
                                raw = raw.decode("utf-8")

                            payload = json.loads(raw)

                            event_type = None
                            user_id = None
                            data = None

                            if isinstance(payload, dict):
                                event_type = payload.get("event_type")
                                data = payload.get("data") or {}

                                # some publishers send user id at top-level
                                user_id = payload.get("user_id") or (data.get("currentUser") if isinstance(data, dict) else None)

                                # unwrap nested data if needed
                                if isinstance(data, dict) and "data" in data:
                                    data = data.get("data") or {}

                            if not event_type or not user_id:
                                print(f"Skipping message missing event_type/currentUser: {payload}")
                                continue

                            message_text = build_message_text(event_type, data)

                            related_id = None
                            if isinstance(data, dict):
                                related_id = data.get("id") or data.get("_id")

                            notification = {
                                "user_id": user_id,
                                "message": message_text,
                                "related_id": related_id,
                                "event_type": event_type,
                                "opened": False,
                                "created_at": datetime.now(),
                            }

                            result = notifications_collection.insert_one(notification)
                            print(f"Inserted notification with ID: {result.inserted_id}")

                        except json.JSONDecodeError as e:
                            print("Invalid JSON in message body:", e)
                        except Exception as e:
                            print("Failed to process notification message:", e)
        except asyncio.CancelledError:
            print("Notification consumer cancelled")


async def consume():
    # Keep the consumer alive if connection drops
    while True:
        try:
            await _consume_once()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"Notification consumer loop error: {exc}; retrying in 5s")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(consume())
    except KeyboardInterrupt:
        print("Interrupted by user")
