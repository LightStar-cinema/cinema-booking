"""
Daily batch report — runs at UTC midnight.

Queries PostgreSQL for the previous day's confirmed bookings and
writes a summary document to the MongoDB `daily_reports` collection.

Usage
─────
Run immediately (yesterday):  python -m workers.daily_report --now
Run for a specific date:       python -m workers.daily_report --date 2025-05-09
Run as midnight daemon:        python -m workers.daily_report
"""
import argparse
import asyncio
import logging
import os
import sys
from datetime import date, datetime, timedelta, timezone

import motor.motor_asyncio
from sqlalchemy import func, select

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.config import settings          # noqa: E402
from core.database import AsyncSessionLocal  # noqa: E402
from models.booking import Booking, BookingSeat, BookingStatus  # noqa: E402
from models.movie import Movie            # noqa: E402
from models.showtime import Showtime      # noqa: E402
from models.user import User              # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("daily_report")


# ── Query helpers ────────────────────────────────────────────────────────────

async def _query_postgres(report_date: date) -> dict:
    """Aggregate the day's confirmed bookings from PostgreSQL."""
    day_start = datetime(report_date.year, report_date.month, report_date.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    async with AsyncSessionLocal() as db:

        # ── Totals ───────────────────────────────────────────────────────
        totals = (await db.execute(
            select(
                func.count(Booking.id.distinct()).label("total_bookings"),
                func.coalesce(func.sum(Booking.total_amount), 0).label("total_revenue"),
                func.count(BookingSeat.id).label("total_tickets"),
            )
            .select_from(Booking)
            .join(BookingSeat, Booking.id == BookingSeat.booking_id)
            .where(
                Booking.status == BookingStatus.CONFIRMED,
                Booking.created_at >= day_start,
                Booking.created_at < day_end,
            )
        )).one()

        # ── Revenue and ticket sales broken down by movie ─────────────────
        movie_rows = (await db.execute(
            select(
                Movie.title,
                func.count(Booking.id.distinct()).label("bookings"),
                func.coalesce(func.sum(Booking.total_amount), 0).label("revenue"),
                func.count(BookingSeat.id).label("tickets_sold"),
            )
            .select_from(Booking)
            .join(Showtime, Booking.showtime_id == Showtime.id)
            .join(Movie, Showtime.movie_id == Movie.id)
            .join(BookingSeat, Booking.id == BookingSeat.booking_id)
            .where(
                Booking.status == BookingStatus.CONFIRMED,
                Booking.created_at >= day_start,
                Booking.created_at < day_end,
            )
            .group_by(Movie.id, Movie.title)
            .order_by(func.sum(Booking.total_amount).desc())
        )).all()

        # ── Cancellations ─────────────────────────────────────────────────
        cancellations = (await db.execute(
            select(func.count(Booking.id)).where(
                Booking.status == BookingStatus.CANCELLED,
                Booking.updated_at >= day_start,
                Booking.updated_at < day_end,
            )
        )).scalar_one()

        # ── New user registrations ────────────────────────────────────────
        new_users = (await db.execute(
            select(func.count(User.id)).where(
                User.created_at >= day_start,
                User.created_at < day_end,
            )
        )).scalar_one()

    return {
        "summary": {
            "total_bookings": totals.total_bookings,
            "total_tickets": totals.total_tickets,
            "total_revenue_usd": float(totals.total_revenue),
            "cancellations": cancellations,
            "new_users": new_users,
        },
        "by_movie": [
            {
                "movie": row.title,
                "bookings": row.bookings,
                "tickets_sold": row.tickets_sold,
                "revenue_usd": float(row.revenue),
            }
            for row in movie_rows
        ],
    }


async def _save_to_mongo(report: dict) -> None:
    """Upsert the report document into MongoDB (idempotent on report_date)."""
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongo_url)
    try:
        col = client[settings.mongo_db]["daily_reports"]
        result = await col.update_one(
            {"report_date": report["report_date"]},
            {"$set": report},
            upsert=True,
        )
        verb = "Inserted" if result.upserted_id else "Updated"
        logger.info("%s report for %s in MongoDB.", verb, report["report_date"])
    finally:
        client.close()


# ── Main entry points ────────────────────────────────────────────────────────

async def run_for_date(report_date: date) -> None:
    logger.info("Generating report for %s …", report_date)
    data = await _query_postgres(report_date)

    report = {
        "report_date": report_date.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **data,
    }

    await _save_to_mongo(report)

    s = report["summary"]
    logger.info(
        "Done — bookings=%d  tickets=%d  revenue=$%.2f  cancellations=%d  new_users=%d",
        s["total_bookings"],
        s["total_tickets"],
        s["total_revenue_usd"],
        s["cancellations"],
        s["new_users"],
    )


async def _midnight_scheduler() -> None:
    """Sleep until the next UTC midnight, generate yesterday's report, repeat."""
    while True:
        now = datetime.now(timezone.utc)
        next_midnight = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        wait_secs = (next_midnight - now).total_seconds()
        logger.info(
            "Next run in %.0fs at %s UTC.",
            wait_secs,
            next_midnight.strftime("%Y-%m-%dT%H:%M:%S"),
        )
        await asyncio.sleep(wait_secs)

        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date()
        try:
            await run_for_date(yesterday)
        except Exception as exc:
            logger.error("Report failed for %s: %s", yesterday, exc, exc_info=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cinema daily batch report")
    parser.add_argument("--now", action="store_true", help="Run once for yesterday and exit")
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        metavar="YYYY-MM-DD",
        help="Run for a specific date and exit",
    )
    args = parser.parse_args()

    if args.now or args.date:
        target = args.date or (datetime.now(timezone.utc) - timedelta(days=1)).date()
        asyncio.run(run_for_date(target))
    else:
        logger.info("Starting midnight scheduler …")
        try:
            asyncio.run(_midnight_scheduler())
        except KeyboardInterrupt:
            logger.info("Scheduler stopped.")
