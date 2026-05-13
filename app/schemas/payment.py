from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from models.payment import PaymentMethod, PaymentStatus


class PaymentCreate(BaseModel):
    booking_id: UUID
    payment_method: PaymentMethod


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    booking_id: UUID
    amount: Decimal
    currency: str
    status: PaymentStatus
    payment_method: PaymentMethod
    transaction_id: str | None
    created_at: datetime
