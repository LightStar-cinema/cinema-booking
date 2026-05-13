import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.deps import get_db, require_admin
from models.booking import Booking, BookingSeat, BookingStatus
from models.screen import Screen
from models.seat import SeatType
from models.showtime import Showtime
from schemas.movie import MovieOut
from schemas.showtime import (
    ScreenOut,
    SeatAvailabilityOut,
    ShowtimeCreate,
    ShowtimeOut,
    ShowtimeWithSeatsOut,
)

router = APIRouter(prefix="/api/showtimes", tags=["showtimes"])


@router.get("", response_model=list[ShowtimeOut])
async def list_showtimes(
    db: Annotated[AsyncSession, Depends(get_db)],
    movie_id: uuid.UUID | None = Query(None),
    show_date: date | None = Query(None, alias="date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    q = (
        select(Showtime)
        .options(selectinload(Showtime.movie), selectinload(Showtime.screen))
        .where(Showtime.is_active == True)  # noqa: E712
        .where(Showtime.start_time > datetime.now(timezone.utc))
    )
    if movie_id:
        q = q.where(Showtime.movie_id == movie_id)
    if show_date:
        day_start = datetime(show_date.year, show_date.month, show_date.day, tzinfo=timezone.utc)
        q = q.where(
            Showtime.start_time >= day_start,
            Showtime.start_time < day_start + timedelta(days=1),
        )
    q = q.order_by(Showtime.start_time).offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{showtime_id}", response_model=ShowtimeWithSeatsOut)
async def get_showtime_with_seats(
    showtime_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Showtime)
        .options(
            selectinload(Showtime.movie),
            selectinload(Showtime.screen).selectinload(Screen.seats),
        )
        .where(Showtime.id == showtime_id)
    )
    showtime = result.scalar_one_or_none()
    if not showtime:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Showtime not found")

    # Seat IDs already reserved by non-cancelled bookings
    booked_result = await db.execute(
        select(BookingSeat.seat_id)
        .join(Booking, BookingSeat.booking_id == Booking.id)
        .where(
            BookingSeat.showtime_id == showtime_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
        )
    )
    booked_ids: set[uuid.UUID] = set(booked_result.scalars().all())

    seat_list: list[SeatAvailabilityOut] = []
    for seat in showtime.screen.seats:
        if not seat.is_active:
            continue
        price = showtime.price_vip if seat.seat_type == SeatType.VIP else showtime.price_regular
        seat_list.append(
            SeatAvailabilityOut(
                seat_id=seat.id,
                row=seat.row,
                number=seat.number,
                seat_type=seat.seat_type,
                is_available=seat.id not in booked_ids,
                price=price,
            )
        )
    # Sort seats by row then number for consistent display
    seat_list.sort(key=lambda s: (s.row, s.number))

    return ShowtimeWithSeatsOut(
        id=showtime.id,
        movie_id=showtime.movie_id,
        screen_id=showtime.screen_id,
        start_time=showtime.start_time,
        end_time=showtime.end_time,
        price_regular=showtime.price_regular,
        price_vip=showtime.price_vip,
        is_active=showtime.is_active,
        movie=MovieOut.model_validate(showtime.movie),
        screen=ScreenOut.model_validate(showtime.screen),
        created_at=showtime.created_at,
        seats=seat_list,
    )


@router.post("", response_model=ShowtimeOut, status_code=status.HTTP_201_CREATED)
async def create_showtime(
    body: ShowtimeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(require_admin)],
):
    if body.end_time <= body.start_time:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "end_time must be after start_time")

    showtime = Showtime(**body.model_dump())
    db.add(showtime)
    await db.commit()

    result = await db.execute(
        select(Showtime)
        .options(selectinload(Showtime.movie), selectinload(Showtime.screen))
        .where(Showtime.id == showtime.id)
    )
    return result.scalar_one()
