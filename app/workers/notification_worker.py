"""
RabbitMQ consumer — booking.confirmed queue.

Simulates sending a booking confirmation email by structured-logging
every field a real mailer would use.

Run locally:  python -m workers.notification_worker
In Docker:    command: ["python", "-m", "workers.notification_worker"]
"""
import asyncio
import json
import logging
import os
import sys

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

# Allow running from any working directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.config import settings  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("notification_worker")

_EXCHANGE = "cinema"
_QUEUE = "booking.confirmed"
_ROUTING_KEY = "booking.confirmed"


async def _handle_booking_confirmed(msg: AbstractIncomingMessage) -> None:
    """Process one booking_confirmed event and simulate an outbound email."""
    async with msg.process(requeue=True):
        try:
            data = json.loads(msg.body)
        except json.JSONDecodeError as exc:
            logger.error("Malformed message body — skipping: %s", exc)
            return

        seats = ", ".join(data.get("seats", []))

        # ── Simulated email ───────────────────────────────────────────────
        logger.info(
            "\n"
            "  ┌─ SIMULATED EMAIL ───────────────────────────────────────┐\n"
            "  │ To      : %s <%s>\n"
            "  │ Subject : Booking Confirmed — %s\n"
            "  ├─────────────────────────────────────────────────────────┤\n"
            "  │ Hi %s,\n"
            "  │\n"
            "  │ Your booking is confirmed!\n"
            "  │   Reference : %s\n"
            "  │   Movie     : %s\n"
            "  │   Screen    : %s\n"
            "  │   Time      : %s\n"
            "  │   Seats     : %s\n"
            "  │   Total     : %s %s\n"
            "  │   Txn ID    : %s\n"
            "  │   Paid at   : %s\n"
            "  └─────────────────────────────────────────────────────────┘",
            data.get("user_full_name", "Customer"),
            data.get("user_email", ""),
            data.get("booking_reference", ""),
            data.get("user_full_name", ""),
            data.get("booking_reference", ""),
            data.get("movie_title", ""),
            data.get("screen_name", ""),
            data.get("showtime_start", ""),
            seats or "N/A",
            data.get("total_amount", "0"),
            data.get("currency", "USD"),
            data.get("transaction_id", ""),
            data.get("paid_at", ""),
        )


async def main() -> None:
    logger.info("Connecting to RabbitMQ …")
    connection = await aio_pika.connect_robust(
        settings.rabbitmq_url,
        reconnect_interval=5,
    )

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        exchange = await channel.declare_exchange(
            _EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True
        )
        queue = await channel.declare_queue(_QUEUE, durable=True)
        await queue.bind(exchange, routing_key=_ROUTING_KEY)

        logger.info("Listening on queue '%s' (exchange='%s', key='%s') …", _QUEUE, _EXCHANGE, _ROUTING_KEY)
        await queue.consume(_handle_booking_confirmed)

        await asyncio.Future()  # block until interrupted


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped.")
