from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from models.screen import ScreenType
from models.seat import SeatType
from schemas.movie import MovieOut


class ScreenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    screen_type: ScreenType
    capacity: int


class ShowtimeCreate(BaseModel):
    movie_id: UUID
    screen_id: UUID
    start_time: datetime
    end_time: datetime
    price_regular: Decimal
    price_vip: Decimal


class ShowtimeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    movie_id: UUID
    screen_id: UUID
    start_time: datetime
    end_time: datetime
    price_regular: Decimal
    price_vip: Decimal
    is_active: bool
    movie: MovieOut
    screen: ScreenOut
    created_at: datetime


class SeatAvailabilityOut(BaseModel):
    seat_id: UUID
    row: str
    number: int
    seat_type: SeatType
    is_available: bool
    price: Decimal


class ShowtimeWithSeatsOut(BaseModel):
    id: UUID
    movie_id: UUID
    screen_id: UUID
    start_time: datetime
    end_time: datetime
    price_regular: Decimal
    price_vip: Decimal
    is_active: bool
    movie: MovieOut
    screen: ScreenOut
    created_at: datetime
    seats: list[SeatAvailabilityOut]
