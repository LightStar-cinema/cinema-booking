from pydantic import BaseModel


class BookingConfirmedEvent(BaseModel):
    """Published to RabbitMQ after a payment completes successfully."""

    event: str = "booking_confirmed"
    booking_id: str
    booking_reference: str
    user_id: str
    user_email: str
    user_full_name: str
    movie_title: str
    screen_name: str
    showtime_start: str   # ISO 8601
    seats: list[str]      # ["A1", "A2"]
    total_amount: str     # string — avoids float precision loss in transit
    currency: str
    transaction_id: str
    paid_at: str          # ISO 8601
