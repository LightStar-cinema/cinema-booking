import enum
from datetime import date

from sqlalchemy import Date, Enum as SAEnum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class MovieRating(str, enum.Enum):
    G = "G"
    PG = "PG"
    PG13 = "PG-13"
    R = "R"
    NC17 = "NC-17"


class Movie(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "movies"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    genre: Mapped[str] = mapped_column(String(100), nullable=False)
    rating: Mapped[MovieRating] = mapped_column(SAEnum(MovieRating), nullable=False)
    language: Mapped[str] = mapped_column(String(50), default="English", nullable=False)
    poster_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    trailer_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    release_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_coming_soon: Mapped[bool] = mapped_column(default=False, nullable=False)

    showtimes: Mapped[list["Showtime"]] = relationship("Showtime", back_populates="movie")
