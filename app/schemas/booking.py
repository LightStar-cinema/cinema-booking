from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from models.booking import BookingStatus
from models.seat import SeatType
from schemas.payment import PaymentOut
from schemas.showtime import ShowtimeOut


class BookingCreate(BaseModel):
    showtime_id: UUID
    seat_ids: list[UUID]


class PromoApplyRequest(BaseModel):
    code: str
    booking_id: UUID


class PromoApplyResponse(BaseModel):
    total_amount: Decimal
    discount_applied: Decimal
    promo_code: str


class BookingSeatOut(BaseModel):
    seat_id: UUID
    row: str
    number: int
    seat_type: SeatType
    price: Decimal


class BookingOut(BaseModel):
    id: UUID
    booking_reference: str
    status: BookingStatus
    total_amount: Decimal
    promo_code: str | None = None
    original_amount: Decimal | None = None
    showtime: ShowtimeOut
    seats: list[BookingSeatOut]
    payment: PaymentOut | None = None
    created_at: datetime
    updated_at: datetime
