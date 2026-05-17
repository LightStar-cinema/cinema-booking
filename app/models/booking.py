# Booking and BookingSeat Database Models
# Database Engineer: Madirimova Nargiza (U2310149)
#
# This file defines TWO of our most important database tables.
#
# TABLE 1: bookings
# Stores one reservation made by one user for one showtime.
#
# Columns:
#   id               — UUID primary key (unique ID for this booking)
#   user_id          — FK to users table (who made this booking)
#   showtime_id      — FK to showtimes table (which showing they booked)
#   status           — ENUM: PENDING, CONFIRMED, or CANCELLED
#                      PENDING  = seats reserved, payment not done yet
#                      CONFIRMED = payment done, booking is valid
#                      CANCELLED = user cancelled or payment failed
#   booking_reference — Short human-readable code (e.g. CN-X7Y9Z2)
#   total_amount     — Total price for all seats combined
#   created_at       — When the booking was created
#   updated_at       — When it was last changed
#
# TABLE 2: booking_seats
# This is the JUNCTION TABLE between bookings and seats.
# One booking can have many seats. One seat can be in many bookings
# (at different showtimes on different days).
# This many-to-many relationship is solved by this junction table.
#
# Columns:
#   id          — UUID primary key
#   booking_id  — FK to bookings table
#   seat_id     — FK to seats table
#   showtime_id — FK to showtimes table (redundant but needed for the UNIQUE constraint)
#   price       — Price per seat AT THE TIME OF BOOKING (snapshot)
#                 Important: if prices change later, this booking is unaffected
#
# THE MOST IMPORTANT CONSTRAINT:
#   UNIQUE(seat_id, showtime_id)
#   This means: the same seat at the same showtime can only appear ONCE.
#   This is the database-level guard against double-booking.
#   Even if the application code has a bug, the database itself
#   will reject any attempt to book the same seat twice.
import enum
import uuid
from decimal import Decimal

from sqlalchemy import Enum as SAEnum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class Booking(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "bookings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    showtime_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("showtimes.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[BookingStatus] = mapped_column(
        SAEnum(BookingStatus), nullable=False, default=BookingStatus.PENDING, index=True
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # Short human-readable reference, e.g. "BK-A3F9X2"
    booking_reference: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    promo_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    original_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="bookings")
    showtime: Mapped["Showtime"] = relationship("Showtime", back_populates="bookings")
    seats: Mapped[list["BookingSeat"]] = relationship(
        "BookingSeat", back_populates="booking", cascade="all, delete-orphan"
    )
    payment: Mapped["Payment | None"] = relationship(
        "Payment", back_populates="booking", uselist=False
    )


class BookingSeat(Base, UUIDMixin):
    __tablename__ = "booking_seats"
    __table_args__ = (
        # Enforces one booking per seat per showtime at the DB level
        UniqueConstraint("seat_id", "showtime_id", name="uq_booking_seat_per_showtime"),
    )

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seats.id", ondelete="RESTRICT"), nullable=False
    )
    showtime_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("showtimes.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Snapshot of the price at time of booking so price changes don't affect history
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    booking: Mapped["Booking"] = relationship("Booking", back_populates="seats")
    seat: Mapped["Seat"] = relationship("Seat", back_populates="booking_seats")
    showtime: Mapped["Showtime"] = relationship("Showtime", back_populates="booking_seats")
