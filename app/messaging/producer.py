"""
Async RabbitMQ producer — thin wrapper around aio-pika.

Design choices:
  • A single robust connection is reused across requests; aio-pika's
    RobustConnection handles reconnects transparently on broker restarts.
  • publish() swallows exceptions so a RabbitMQ outage never rolls back
    a committed payment — the DB is already the source of truth.
  • close() is called from the FastAPI lifespan shutdown hook.
"""
import json
import logging
from typing import Any

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message

from core.config import settings

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "cinema"

_connection: aio_pika.abc.AbstractRobustConnection | None = None


async def _get_connection() -> aio_pika.abc.AbstractRobustConnection:
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    return _connection


async def publish(routing_key: str, payload: dict[str, Any]) -> None:
    """Publish a JSON message to the cinema topic exchange."""
    try:
        conn = await _get_connection()
        async with conn.channel() as channel:
            exchange = await channel.declare_exchange(
                EXCHANGE_NAME, ExchangeType.TOPIC, durable=True
            )
            await exchange.publish(
                Message(
                    body=json.dumps(payload).encode(),
                    delivery_mode=DeliveryMode.PERSISTENT,
                    content_type="application/json",
                ),
                routing_key=routing_key,
            )
        logger.info("Published [%s] event=%s", routing_key, payload.get("event"))
    except Exception as exc:
        logger.error("RabbitMQ publish failed (key=%s): %s", routing_key, exc)


async def close() -> None:
    """Graceful shutdown — called from the FastAPI lifespan."""
    global _connection
    if _connection and not _connection.is_closed:
        await _connection.close()
        _connection = None
        logger.info("RabbitMQ connection closed.")
