import enum
import uuid

from sqlalchemy import Enum as SAEnum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin


class SeatType(str, enum.Enum):
    REGULAR = "REGULAR"
    VIP = "VIP"
    HANDICAP = "HANDICAP"


class Seat(Base, UUIDMixin):
    __tablename__ = "seats"
    __table_args__ = (
        UniqueConstraint("screen_id", "row", "number", name="uq_seat_screen_row_number"),
    )

    screen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("screens.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Row label, e.g. "A", "B", "AA"
    row: Mapped[str] = mapped_column(String(5), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    seat_type: Mapped[SeatType] = mapped_column(
        SAEnum(SeatType), nullable=False, default=SeatType.REGULAR
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    screen: Mapped["Screen"] = relationship("Screen", back_populates="seats")
    booking_seats: Mapped[list["BookingSeat"]] = relationship("BookingSeat", back_populates="seat")
