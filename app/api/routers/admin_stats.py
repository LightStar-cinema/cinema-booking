from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, require_admin
from models.booking import Booking, BookingSeat, BookingStatus
from models.movie import Movie
from models.showtime import Showtime
from models.user import User

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats/weekly")
async def weekly_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
):
    """Return ticket sales and revenue for the last 7 days. Admin only."""
    week_start = datetime.now(timezone.utc) - timedelta(days=7)

    totals = (await db.execute(
        select(
            func.coalesce(func.sum(Booking.total_amount), 0).label("revenue"),
            func.count(BookingSeat.id).label("tickets"),
        )
        .select_from(Booking)
        .join(BookingSeat, Booking.id == BookingSeat.booking_id)
        .where(
            Booking.status == BookingStatus.CONFIRMED,
            Booking.created_at >= week_start,
        )
    )).one()

    rows = (await db.execute(
        select(
            Movie.title,
            func.count(BookingSeat.id).label("tickets"),
            func.coalesce(func.sum(Booking.total_amount), 0).label("revenue"),
        )
        .select_from(Booking)
        .join(Showtime, Booking.showtime_id == Showtime.id)
        .join(Movie, Showtime.movie_id == Movie.id)
        .join(BookingSeat, Booking.id == BookingSeat.booking_id)
        .where(
            Booking.status == BookingStatus.CONFIRMED,
            Booking.created_at >= week_start,
        )
        .group_by(Movie.id, Movie.title)
        .order_by(func.count(BookingSeat.id).desc())
    )).all()

    by_movie = [
        {"title": r.title, "tickets": r.tickets, "revenue": float(r.revenue)}
        for r in rows
    ]

    return {
        "period_days": 7,
        "total_revenue_usd": float(totals.revenue),
        "total_tickets": totals.tickets,
        "most_popular_movie": by_movie[0]["title"] if by_movie else None,
        "by_movie": by_movie,
    }
