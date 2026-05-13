import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class Showtime(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "showtimes"
    __table_args__ = (
        # One screen cannot host two showtimes starting at the same time
        UniqueConstraint("screen_id", "start_time", name="uq_showtime_screen_start"),
    )

    movie_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("movies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    screen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("screens.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price_regular: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_vip: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    movie: Mapped["Movie"] = relationship("Movie", back_populates="showtimes")
    screen: Mapped["Screen"] = relationship("Screen", back_populates="showtimes")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="showtime")
    booking_seats: Mapped[list["BookingSeat"]] = relationship("BookingSeat", back_populates="showtime")
