import enum
import uuid
from decimal import Decimal

from sqlalchemy import Enum as SAEnum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentMethod(str, enum.Enum):
    CARD = "CARD"
    PAYPAL = "PAYPAL"
    WALLET = "WALLET"


class Payment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payments"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING, index=True
    )
    payment_method: Mapped[PaymentMethod] = mapped_column(SAEnum(PaymentMethod), nullable=False)
    # External gateway transaction ID
    transaction_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    # Raw gateway response stored as JSON string for audit trail
    gateway_response: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    booking: Mapped["Booking"] = relationship("Booking", back_populates="payment")
