# Payments Router — Processing Payments
# API Documentation: Ergasheva Fotima (U2310076)
#
# This file handles payment processing for bookings.
#
# ENDPOINT 1: POST /api/payments
# What it does: Processes a payment and confirms the booking
# Who can use it: Logged-in users only (JWT token required)
# Request body:
#   {
#     "booking_id": "uuid of the pending booking",
#     "payment_method": "CARD",
#     "card_number": "4242424242424242",
#     "expiry_month": 12,
#     "expiry_year": 2027,
#     "cvv": "123"
#   }
# Response:
#   {
#     "id": "payment-uuid",
#     "status": "COMPLETED",
#     "transaction_id": "TXN-12345",
#     "amount": 30.00
#   }
# Error codes:
#   400 — invalid card details
#   403 — booking does not belong to this user
#   404 — booking not found
#   409 — booking already paid or cancelled
#
# WHAT HAPPENS AFTER SUCCESSFUL PAYMENT:
# 1. Payment record created in PostgreSQL (status: COMPLETED)
# 2. Booking status updated to CONFIRMED in PostgreSQL
# 3. booking_confirmed event published to RabbitMQ
# 4. notification_worker picks up the event and logs simulated email
# 5. HTTP 201 response returned to frontend with payment details
#
# ENDPOINT 2: GET /api/payments/{id}
# What it does: Returns details of one payment
# Who can use it: Owner of the payment only
# Response: Full payment object with status, amount, transaction ID
# Error codes:
#   403 — not your payment
#   404 — payment not found
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.deps import get_current_user, get_db
from messaging.producer import publish
from messaging.schemas import BookingConfirmedEvent
from models.booking import Booking, BookingSeat, BookingStatus
from models.payment import Payment, PaymentStatus
from models.seat import Seat
from models.showtime import Showtime
from models.user import User
from schemas.payment import PaymentCreate, PaymentOut

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
async def process_payment(
    body: PaymentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    # ── Validate booking ownership and status ────────────────────────────────
    booking_result = await db.execute(
        select(Booking).where(
            Booking.id == body.booking_id,
            Booking.user_id == current_user.id,
        )
    )
    booking = booking_result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Booking status is '{booking.status}', payment not applicable",
        )

    existing = await db.execute(select(Payment).where(Payment.booking_id == booking.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Payment already exists for this booking")

    # ── Simulated gateway — swap for Stripe/PayPal SDK in production ─────────
    transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"

    payment = Payment(
        booking_id=booking.id,
        amount=booking.total_amount,
        currency="USD",
        status=PaymentStatus.COMPLETED,
        payment_method=body.payment_method,
        transaction_id=transaction_id,
        gateway_response='{"simulated": true, "status": "success"}',
    )
    db.add(payment)
    booking.status = BookingStatus.CONFIRMED
    await db.commit()
    await db.refresh(payment)

    # ── Publish booking_confirmed event to RabbitMQ ──────────────────────────
    # Load the full graph needed to build a rich event payload.
    # Done after commit so the event is only published on durable success.
    enriched = await db.execute(
        select(Booking)
        .options(
            selectinload(Booking.seats).selectinload(BookingSeat.seat),
            selectinload(Booking.showtime).selectinload(Showtime.movie),
            selectinload(Booking.showtime).selectinload(Showtime.screen),
        )
        .where(Booking.id == booking.id)
    )
    b = enriched.scalar_one()

    event = BookingConfirmedEvent(
        booking_id=str(b.id),
        booking_reference=b.booking_reference,
        user_id=str(current_user.id),
        user_email=current_user.email,
        user_full_name=current_user.full_name,
        movie_title=b.showtime.movie.title,
        screen_name=b.showtime.screen.name,
        showtime_start=b.showtime.start_time.isoformat(),
        seats=[f"{bs.seat.row}{bs.seat.number}" for bs in b.seats],
        total_amount=str(b.total_amount),
        currency=payment.currency,
        transaction_id=payment.transaction_id,
        paid_at=payment.created_at.isoformat(),
    )
    await publish("booking.confirmed", event.model_dump())

    return payment


@router.get("/{payment_id}", response_model=PaymentOut)
async def get_payment(
    payment_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Payment)
        .join(Booking, Payment.booking_id == Booking.id)
        .where(Payment.id == payment_id, Booking.user_id == current_user.id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment not found")
    return payment
