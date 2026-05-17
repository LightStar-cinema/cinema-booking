
# =============================================================================
# bookings.py — Booking Router
# Written by: Hazratov Sardorbek (U2310090)
#
# This file handles everything related to seat reservations.
#
# How booking works step by step:
# Step 1: User sends POST /api/bookings with showtime_id and seat_ids
# Step 2: We check the JWT token — is the user logged in?
# Step 3: We check the rate limiter — did this user book too many times?
# Step 4: We run a Redis Lua script to lock all the seats atomically
#         If ANY seat is already locked → return 409 Conflict immediately
# Step 5: We write a PENDING booking to PostgreSQL
# Step 6: We return the booking details to the frontend
#
# The double-booking prevention has TWO layers:
# Layer 1 (fast): Redis lock with 30 second TTL
#   - Blocks anyone else from selecting the seat while you are booking
# Layer 2 (final): PostgreSQL UNIQUE(seat_id, showtime_id) constraint
#   - Even if Redis fails, the database will reject a duplicate
#
# Endpoints in this file:
# POST   /api/bookings          — Reserve seats
# GET    /api/bookings/me       — My booking history
# GET    /api/bookings/{id}     — One booking detail
# POST   /api/bookings/{id}/cancel — Cancel a booking
# =============================================================================


import random
import string
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.deps import get_current_user, get_db, get_redis
from api.ws_manager import manager as ws_manager
from components.rate_limiter import TokenBucketLimiter
from core import telemetry
from models.booking import Booking, BookingSeat, BookingStatus
from models.seat import Seat, SeatType
from models.showtime import Showtime
from models.user import User
from schemas.booking import BookingCreate, BookingOut, BookingSeatOut, PromoApplyRequest, PromoApplyResponse
from schemas.movie import MovieOut
from schemas.payment import PaymentOut
from schemas.showtime import ShowtimeOut

router = APIRouter(prefix="/api/bookings", tags=["bookings"])

# 5 booking attempts per user per 60 s — dependency called once at import time
# so FastAPI can deduplicate the get_current_user sub-dependency.
_booking_limit = TokenBucketLimiter(capacity=5, window_seconds=60, key_prefix="booking")
_check_booking_rate = _booking_limit.limit_by_user()

# ── Redis Lua scripts ────────────────────────────────────────────────────────
# Lua executes atomically inside Redis — no other command can interleave.
# _LOCK_SCRIPT: checks ALL keys are free before setting any; aborts cleanly if not.
# _UNLOCK_SCRIPT: only deletes keys whose value matches the caller's token,
#                 preventing a stale unlock from a previous owner.

_LOCK_SCRIPT = """
for i = 1, #KEYS do
    if redis.call('EXISTS', KEYS[i]) == 1 then
        return 0
    end
end
for i = 1, #KEYS do
    redis.call('SET', KEYS[i], ARGV[1], 'EX', tonumber(ARGV[2]))
end
return 1
"""

_UNLOCK_SCRIPT = """
for i = 1, #KEYS do
    if redis.call('GET', KEYS[i]) == ARGV[1] then
        redis.call('DEL', KEYS[i])
    end
end
return 1
"""

_LOCK_TTL = 30  # seconds — covers the DB round-trip, not the payment flow


# ── Helpers ──────────────────────────────────────────────────────────────────

def _lock_keys(showtime_id: uuid.UUID, seat_ids: list[uuid.UUID]) -> list[str]:
    return [f"seat_lock:{showtime_id}:{sid}" for sid in sorted(str(s) for s in seat_ids)]


def _new_reference() -> str:
    chars = string.ascii_uppercase + string.digits
    return "BK-" + "".join(random.choices(chars, k=6))


def _seat_event(showtime_id: str, seat_ids: list[str], seat_status: str) -> dict:
    return {
        "event": "seat_status",
        "showtime_id": showtime_id,
        "seats": [{"seat_id": sid, "status": seat_status} for sid in seat_ids],
    }


async def _load_booking(db: AsyncSession, booking_id: uuid.UUID) -> Booking | None:
    result = await db.execute(
        select(Booking)
        .options(
            selectinload(Booking.seats).selectinload(BookingSeat.seat),
            selectinload(Booking.payment),
            selectinload(Booking.showtime).selectinload(Showtime.movie),
            selectinload(Booking.showtime).selectinload(Showtime.screen),
        )
        .where(Booking.id == booking_id)
    )
    return result.scalar_one_or_none()


_PROMO_CODES: dict[str, tuple[str, Decimal]] = {
    "CINE10":  ("percent", Decimal("10")),
    "CINE20":  ("percent", Decimal("20")),
    "STUDENT": ("percent", Decimal("15")),
    "IMAX5":   ("fixed",   Decimal("5")),
}


def _to_out(booking: Booking) -> BookingOut:
    return BookingOut(
        id=booking.id,
        booking_reference=booking.booking_reference,
        status=booking.status,
        total_amount=booking.total_amount,
        promo_code=booking.promo_code,
        original_amount=booking.original_amount,
        showtime=ShowtimeOut.model_validate(booking.showtime),
        seats=[
            BookingSeatOut(
                seat_id=bs.seat_id,
                row=bs.seat.row,
                number=bs.seat.number,
                seat_type=bs.seat.seat_type,
                price=bs.price,
            )
            for bs in booking.seats
        ],
        payment=PaymentOut.model_validate(booking.payment) if booking.payment else None,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
    )


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def create_booking(
    body: BookingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
    _rl: Annotated[None, Depends(_check_booking_rate)],
):
    if not body.seat_ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "At least one seat must be selected")

    # ── 1. Validate showtime ─────────────────────────────────────────────────
    st_result = await db.execute(
        select(Showtime).where(Showtime.id == body.showtime_id, Showtime.is_active == True)  # noqa: E712
    )
    showtime = st_result.scalar_one_or_none()
    if not showtime:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Showtime not found or inactive")
    if showtime.start_time <= datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot book seats for a past showtime")

    # ── 2. Validate seats belong to this showtime's screen ───────────────────
    seat_result = await db.execute(
        select(Seat).where(
            Seat.id.in_(body.seat_ids),
            Seat.screen_id == showtime.screen_id,
            Seat.is_active == True,  # noqa: E712
        )
    )
    seats = list(seat_result.scalars().all())
    if len(seats) != len(set(body.seat_ids)):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "One or more seat IDs are invalid or not in this showtime's screen",
        )

    # ── 3. Acquire Redis locks (atomic, all-or-nothing) ──────────────────────
    lock_keys = _lock_keys(body.showtime_id, body.seat_ids)
    lock_token = str(uuid.uuid4())
    acquired = await redis.eval(_LOCK_SCRIPT, len(lock_keys), *lock_keys, lock_token, str(_LOCK_TTL))
    if not acquired:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "One or more seats are currently being reserved. Please try again shortly.",
        )

    # ── 4. Broadcast "locked" to WebSocket viewers ───────────────────────────
    room = str(body.showtime_id)
    seat_ids_str = [str(sid) for sid in body.seat_ids]
    await ws_manager.broadcast(room, _seat_event(room, seat_ids_str, "locked"))

    # ── 5. DB operations inside a try/finally that always releases the lock ──
    committed = False
    booking_id: uuid.UUID | None = None
    try:
        # Hard DB check — catches races that slipped past the Redis lock
        conflict_result = await db.execute(
            select(BookingSeat.seat_id)
            .join(Booking, BookingSeat.booking_id == Booking.id)
            .where(
                BookingSeat.seat_id.in_(body.seat_ids),
                BookingSeat.showtime_id == body.showtime_id,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            )
        )
        conflicted = conflict_result.scalars().all()
        if conflicted:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"{len(conflicted)} seat(s) already booked for this showtime",
            )

        # Calculate total (price snapshotted at booking time)
        seat_map = {s.id: s for s in seats}
        line_items: list[tuple[Seat, Decimal]] = []
        total = Decimal("0")
        for sid in body.seat_ids:
            seat = seat_map[sid]
            price = showtime.price_vip if seat.seat_type == SeatType.VIP else showtime.price_regular
            total += price
            line_items.append((seat, price))

        # Persist booking + seats
        booking = Booking(
            user_id=current_user.id,
            showtime_id=body.showtime_id,
            status=BookingStatus.PENDING,
            total_amount=total,
            booking_reference=_new_reference(),
        )
        db.add(booking)
        await db.flush()  # resolves booking.id before inserting child rows

        booking_id = booking.id  # capture before commit expires the instance

        for seat, price in line_items:
            db.add(
                BookingSeat(
                    booking_id=booking.id,
                    seat_id=seat.id,
                    showtime_id=body.showtime_id,
                    price=price,
                )
            )
        await db.commit()
        committed = True

        if telemetry.bookings_created:
            telemetry.bookings_created.add(1)

    finally:
        # Always release Redis locks, then broadcast the final seat state
        await redis.eval(_UNLOCK_SCRIPT, len(lock_keys), *lock_keys, lock_token)
        final_status = "booked" if committed else "available"
        await ws_manager.broadcast(room, _seat_event(room, seat_ids_str, final_status))

    booking = await _load_booking(db, booking_id)
    return _to_out(booking)


@router.get("/me", response_model=list[BookingOut])
async def my_bookings(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    result = await db.execute(
        select(Booking)
        .options(
            selectinload(Booking.seats).selectinload(BookingSeat.seat),
            selectinload(Booking.payment),
            selectinload(Booking.showtime).selectinload(Showtime.movie),
            selectinload(Booking.showtime).selectinload(Showtime.screen),
        )
        .where(Booking.user_id == current_user.id)
        .order_by(Booking.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return [_to_out(b) for b in result.scalars().all()]


@router.post("/apply-promo", response_model=PromoApplyResponse)
async def apply_promo(
    body: PromoApplyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    booking = await _load_booking(db, body.booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Promo codes can only be applied to pending bookings")
    if booking.promo_code:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A promo code has already been applied to this booking")

    code = body.code.strip().upper()
    if code not in _PROMO_CODES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid promo code")

    discount_type, discount_value = _PROMO_CODES[code]
    original = booking.total_amount
    if discount_type == "percent":
        discount = (original * discount_value / Decimal("100")).quantize(Decimal("0.01"))
    else:
        discount = min(discount_value, original)

    booking.original_amount = original
    booking.promo_code = code
    booking.total_amount = original - discount
    await db.commit()

    return PromoApplyResponse(
        total_amount=booking.total_amount,
        discount_applied=discount,
        promo_code=code,
    )


@router.get("/{booking_id}", response_model=BookingOut)
async def get_booking(
    booking_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    booking = await _load_booking(db, booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    return _to_out(booking)


@router.post("/{booking_id}/cancel", response_model=BookingOut)
async def cancel_booking(
    booking_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    booking = await _load_booking(db, booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    if booking.status not in {BookingStatus.PENDING, BookingStatus.CONFIRMED}:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Cannot cancel a booking with status '{booking.status}'",
        )

    # Capture identifiers before commit expires the ORM instance
    room = str(booking.showtime_id)
    seat_ids_str = [str(bs.seat_id) for bs in booking.seats]

    booking.status = BookingStatus.CANCELLED
    await db.commit()

    # Freed seats become available for others — broadcast immediately
    await ws_manager.broadcast(room, _seat_event(room, seat_ids_str, "available"))

    return _to_out(await _load_booking(db, booking_id))
