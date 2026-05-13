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
