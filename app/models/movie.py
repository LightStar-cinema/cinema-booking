# =============================================================================
# Movie Database Model
# Database Engineer: Madirimova Nargiza (U2310149)
#
# This file defines the movies table in PostgreSQL.
#
# TABLE: movies
# Stores the entire film catalogue for CineLuxe.
#
# Columns:
#   id             — UUID primary key
#   title          — Movie name (e.g. "Inception")
#   description    — Plot summary shown on the movie details page
#   genre          — Category (Action, Drama, Sci-Fi, etc.)
#   duration_minutes — How long the movie is (used to calculate end_time)
#   rating         — Age rating ENUM: G, PG, PG-13, R, NC-17
#   release_date   — When the movie was released (or will be released)
#   language       — Language of the film
#   poster_url     — Path to the poster image file
#   is_active      — Boolean: true = showing now, false = hidden from listing
#   is_coming_soon — Boolean: true = upcoming film (shows in Coming Soon section)
#   created_at     — Auto timestamp
#   updated_at     — Auto timestamp (updated every time movie is changed)
#
# DESIGN DECISIONS:
#
# Why is_active instead of deleting?
#   We use "soft delete" — setting is_active=false instead of actually
#   deleting the row. This preserves historical data (bookings still
#   reference the movie even after it stops showing).
#
# Why ENUM for rating?
#   ENUM types only allow specific values: G, PG, PG-13, R, NC-17.
#   This prevents typos like "Pg-13" or "pg13" being saved.
#
# RELATIONSHIPS:
#   One movie can have MANY showtimes (one-to-many)
# =============================================================================
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
