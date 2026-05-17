# =============================================================================
# User Database Model
# Database Engineer: Madirimova Nargiza (U2310149)
#
# This file defines the users table in PostgreSQL.
#
# TABLE: users
# Stores every person who has registered on CineLuxe.
#
# Columns:
#   id              — UUID primary key
#                     Why UUID and not 1,2,3?
#                     Because sequential IDs let people guess other users' IDs.
#                     UUIDs are random 36-character strings — impossible to guess.
#
#   email           — The user's email address (UNIQUE constraint)
#                     UNIQUE means no two users can have the same email.
#                     This is enforced at database level.
#
#   hashed_password — Password stored as a bcrypt hash, NOT plain text.
#                     Even if someone steals the database, they cannot see passwords.
#
#   full_name       — User's display name
#
#   phone           — Optional phone number (can be NULL)
#
#   is_active       — Boolean (true/false)
#                     If false, user cannot log in (account disabled)
#
#   is_admin        — Boolean (true/false)
#                     If true, user can access admin-only endpoints
#                     (add movies, view stats, etc.)
#
#   created_at      — Timestamp when account was created (auto-set)
#   updated_at      — Timestamp when account was last changed (auto-updated)
#
# RELATIONSHIPS:
#   One user can have MANY bookings (one-to-many)
#   Accessed via: user.bookings
#
# SEED DATA (test accounts):
#   Admin: admin@cinema.com / Admin1234!
#   User1: alice@example.com / Alice1234!
#   User2: bob@example.com / Bob12345!
# =============================================================================
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="user")
