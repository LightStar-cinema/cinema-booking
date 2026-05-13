from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from models.movie import MovieRating


class MovieCreate(BaseModel):
    title: str
    description: str | None = None
    duration_minutes: int
    genre: str
    rating: MovieRating
    language: str = "English"
    poster_url: str | None = None
    trailer_url: str | None = None
    release_date: date
    is_coming_soon: bool = False


class MovieUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    duration_minutes: int | None = None
    genre: str | None = None
    rating: MovieRating | None = None
    language: str | None = None
    poster_url: str | None = None
    trailer_url: str | None = None
    release_date: date | None = None
    is_active: bool | None = None
    is_coming_soon: bool | None = None


class MovieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    duration_minutes: int
    genre: str
    rating: MovieRating
    language: str
    poster_url: str | None
    trailer_url: str | None
    release_date: date
    is_active: bool
    is_coming_soon: bool
    created_at: datetime
    updated_at: datetime
