#!/usr/bin/env python3
"""
Database seed script — populates sample data for development and demo.

Run inside the API container:
    docker compose exec api python scripts/seed.py

Re-running is safe: checks for existing admin user and skips if found.
"""
import asyncio
import os
import sys
from datetime import date as date_type
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import bcrypt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import settings
from models.movie import Movie, MovieRating
from models.screen import Screen, ScreenType
from models.seat import Seat, SeatType
from models.showtime import Showtime
from models.user import User

engine = create_async_engine(settings.database_url, echo=False)
Session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


def _hash(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


# ── Data definitions ──────────────────────────────────────────────────────────

USERS = [
    {
        "email": "admin@cinema.com",
        "password": "Admin1234!",
        "full_name": "Admin User",
        "is_admin": True,
    },
    {
        "email": "alice@example.com",
        "password": "Alice1234!",
        "full_name": "Alice Johnson",
    },
    {
        "email": "bob@example.com",
        "password": "Bob12345!",
        "full_name": "Bob Smith",
    },
]

MOVIES = [
    {
        "title": "Dune: Part Two",
        "description": (
            "Paul Atreides unites with Chani and the Fremen while on a warpath of revenge "
            "against the conspirators who destroyed his family. Facing a choice between the "
            "love of his life and the fate of the known universe, he must prevent a terrible "
            "future only he can foresee."
        ),
        "duration_minutes": 166,
        "genre": "Sci-Fi",
        "rating": MovieRating.PG13,
        "release_date": date_type(2024, 3, 1),
        "poster_url": "/images/dune.jpg",
    },
    {
        "title": "Oppenheimer",
        "description": (
            "The story of American scientist J. Robert Oppenheimer and his role in the "
            "development of the atomic bomb during World War II. A gripping portrait of "
            "the brilliant and conflicted genius who changed the world forever."
        ),
        "duration_minutes": 180,
        "genre": "Biography",
        "rating": MovieRating.R,
        "release_date": date_type(2023, 7, 21),
        "poster_url": "/images/oppenheimer.jpg",
    },
    {
        "title": "The Dark Knight",
        "description": (
            "When the menace known as the Joker wreaks havoc and chaos on the people of "
            "Gotham, Batman must accept one of the greatest psychological and physical "
            "tests of his ability to fight injustice."
        ),
        "duration_minutes": 152,
        "genre": "Action",
        "rating": MovieRating.PG13,
        "release_date": date_type(2008, 7, 18),
        "poster_url": "/images/darkknight.jpg",
    },
    {
        "title": "Interstellar",
        "description": (
            "A team of explorers travel through a wormhole in space in an attempt to "
            "ensure humanity's survival. An epic journey through the cosmos that explores "
            "the boundaries of human ingenuity and love."
        ),
        "duration_minutes": 169,
        "genre": "Sci-Fi",
        "rating": MovieRating.PG13,
        "release_date": date_type(2014, 11, 7),
        "poster_url": "/images/interstellar.jpg",
    },
    {
        "title": "Inception",
        "description": (
            "A thief who steals corporate secrets through the use of dream-sharing technology "
            "is given the inverse task of planting an idea into the mind of a C.E.O. "
            "A mind-bending thriller that questions the nature of reality itself."
        ),
        "duration_minutes": 148,
        "genre": "Sci-Fi",
        "rating": MovieRating.PG13,
        "release_date": date_type(2010, 7, 16),
        "poster_url": "/images/inception.jpg",
    },
    {
        "title": "The Batman",
        "description": (
            "Batman ventures into Gotham City's underworld when a sadistic killer leaves "
            "behind a trail of cryptic clues. A dark and gritty reinvention of the Caped "
            "Crusader that explores the detective side of the legendary hero."
        ),
        "duration_minutes": 176,
        "genre": "Crime",
        "rating": MovieRating.PG13,
        "release_date": date_type(2022, 3, 4),
        "poster_url": "/images/batman.jpg",
    },
    {
        "title": "Avatar: The Way of Water",
        "description": (
            "Jake Sully lives with his newfound family formed on the planet of Pandora. "
            "A visually breathtaking sequel that expands the world of Pandora with stunning "
            "underwater sequences and deep emotional storytelling."
        ),
        "duration_minutes": 192,
        "genre": "Adventure",
        "rating": MovieRating.PG13,
        "release_date": date_type(2022, 12, 16),
        "poster_url": "/images/avatar.jpg",
    },
    {
        "title": "Top Gun: Maverick",
        "description": (
            "After more than thirty years of service as one of the Navy's top aviators, "
            "Pete Mitchell is where he belongs — pushing the envelope as a courageous test "
            "pilot. A spectacular return to the skies with breathtaking aerial sequences."
        ),
        "duration_minutes": 130,
        "genre": "Action",
        "rating": MovieRating.PG13,
        "release_date": date_type(2022, 5, 27),
        "poster_url": "/images/topgun.jpg",
    },
]

# Poster URL lookup for UPDATE path (title → url)
POSTER_URLS = {m["title"]: m["poster_url"] for m in MOVIES}

# ── Coming soon (not yet showing, is_active=False, is_coming_soon=True) ───────
# Avatar: Fire and Ash removed — release date has passed.
COMING_SOON = [
    {
        "title": "Avengers: Doomsday",
        "description": (
            "The Avengers face their greatest threat yet as a new villain with unimaginable "
            "power threatens to reshape the fabric of reality itself. Earth's mightiest heroes "
            "must unite like never before to stop the coming apocalypse."
        ),
        "duration_minutes": 150,
        "genre": "Action",
        "rating": MovieRating.PG13,
        "release_date": date_type(2026, 5, 1),
        "poster_url": "/images/doomsday.jpg",
        "is_coming_soon": True,
        "is_active": False,
    },
    {
        "title": "Spider-Man: Brand New Day",
        "description": (
            "Peter Parker swings into a brand new chapter, facing enemies from across the "
            "multiverse in a battle that will redefine what it means to be Spider-Man. "
            "With great power comes an even greater responsibility."
        ),
        "duration_minutes": 135,
        "genre": "Action",
        "rating": MovieRating.PG13,
        "release_date": date_type(2026, 7, 24),
        "poster_url": "/images/spiderman.jpg",
        "is_coming_soon": True,
        "is_active": False,
    },
]

# Titles to DELETE from the database (removed from seed data)
MOVIES_TO_DELETE = ["Avatar: Fire and Ash"]

# Coming-soon poster lookup — auto-derived for the update path
COMING_SOON_POSTER_URLS = {m["title"]: m["poster_url"] for m in COMING_SOON}

# (name, ScreenType, capacity)
SCREENS = [
    ("Standard Hall 1", ScreenType.STANDARD, 100),
    ("IMAX Experience", ScreenType.IMAX,     100),
    ("Luxe VIP Suite",  ScreenType.DOLBY,    100),
]

# Seat layout rules per screen index:
# 0 = Standard: rows A-H regular, row I seats 9-10 handicap, row J regular
# 1 = IMAX:     rows A-G regular, rows H-J VIP
# 2 = VIP:      row A seats 1-2 handicap, rest VIP
def seat_type_for(screen_idx: int, row: str, number: int) -> SeatType:
    if screen_idx == 0:
        if row == "I" and number >= 9:
            return SeatType.HANDICAP
        return SeatType.REGULAR
    if screen_idx == 1:
        return SeatType.VIP if row in "HIJ" else SeatType.REGULAR
    # screen_idx == 2 (VIP Suite)
    if row == "A" and number <= 2:
        return SeatType.HANDICAP
    return SeatType.VIP


# Prices per screen index: (price_regular, price_vip)
PRICES = [
    (Decimal("12.50"), Decimal("15.00")),  # Standard
    (Decimal("18.00"), Decimal("22.00")),  # IMAX
    (Decimal("22.00"), Decimal("28.00")),  # VIP Suite
]

# Showtime schedule: (day_offset, hour, minute, screen_idx, movie_idx)
# 20 showtimes spread over 7 days across 3 screens
SCHEDULE = [
    # Day 1
    (0, 10, 30, 0, 0),  # Standard — Dune Part Two
    (0, 14,  0, 1, 1),  # IMAX     — Oppenheimer
    (0, 19,  0, 2, 2),  # VIP      — The Dark Knight
    # Day 2
    (1, 11,  0, 0, 3),  # Standard — Interstellar
    (1, 15, 30, 1, 4),  # IMAX     — Inception
    (1, 20,  0, 2, 5),  # VIP      — The Batman
    # Day 3
    (2, 10, 30, 0, 6),  # Standard — Avatar
    (2, 14,  0, 1, 7),  # IMAX     — Top Gun: Maverick
    (2, 19, 30, 2, 0),  # VIP      — Dune Part Two
    # Day 4
    (3, 12,  0, 0, 1),  # Standard — Oppenheimer
    (3, 16,  0, 1, 2),  # IMAX     — The Dark Knight
    (3, 20,  0, 2, 3),  # VIP      — Interstellar
    # Day 5
    (4, 10, 30, 0, 4),  # Standard — Inception
    (4, 14,  0, 1, 5),  # IMAX     — The Batman
    (4, 19,  0, 2, 6),  # VIP      — Avatar
    # Day 6
    (5, 11,  0, 0, 7),  # Standard — Top Gun: Maverick
    (5, 15,  0, 1, 0),  # IMAX     — Dune Part Two
    (5, 19, 30, 2, 1),  # VIP      — Oppenheimer
    # Day 7
    (6, 10, 30, 0, 2),  # Standard — The Dark Knight
    (6, 18,  0, 2, 3),  # VIP      — Interstellar
]


# ── Main seed function ────────────────────────────────────────────────────────

async def seed() -> None:
    async with Session() as db:

        # Idempotency check
        if (await db.execute(select(User).where(User.email == "admin@cinema.com"))).scalar_one_or_none():
            print("Database already seeded. Applying patches…")
            changed = 0

            # 1. Force-update ALL main-movie poster URLs (always overwrite)
            for title, url in POSTER_URLS.items():
                movie = (await db.execute(select(Movie).where(Movie.title == title))).scalar_one_or_none()
                if movie:
                    movie.poster_url = url
                    changed += 1

            # 2. Force-update / insert coming-soon movies
            for m in COMING_SOON:
                exists = (await db.execute(select(Movie).where(Movie.title == m["title"]))).scalar_one_or_none()
                if exists:
                    exists.poster_url = COMING_SOON_POSTER_URLS[m["title"]]  # always overwrite
                    changed += 1
                else:
                    db.add(Movie(**m, language="English"))
                    changed += 1

            # 3. Delete movies that are no longer in the seed data
            from sqlalchemy import delete as sa_delete
            for title in MOVIES_TO_DELETE:
                result = await db.execute(sa_delete(Movie).where(Movie.title == title))
                if result.rowcount:
                    print(f"  ✓ Deleted '{title}'")
                    changed += 1

            await db.commit()
            print(f"  ✓ {changed} record(s) patched/inserted/deleted")
            return

        print("Seeding database…\n")

        # ── Users ────────────────────────────────────────────────────
        users = []
        for u in USERS:
            user = User(
                email=u["email"],
                hashed_password=_hash(u["password"]),
                full_name=u["full_name"],
                is_admin=u.get("is_admin", False),
                is_active=True,
            )
            db.add(user)
            users.append(user)
        await db.flush()
        print(f"  ✓ {len(users)} users")

        # ── Movies ───────────────────────────────────────────────────
        movies = []
        for m in MOVIES:
            movie = Movie(**m, language="English", is_active=True)
            db.add(movie)
            movies.append(movie)
        for m in COMING_SOON:
            db.add(Movie(**m, language="English"))
        await db.flush()
        print(f"  ✓ {len(movies)} now-showing + {len(COMING_SOON)} coming-soon movies")

        # ── Screens ──────────────────────────────────────────────────
        screens = []
        for name, screen_type, capacity in SCREENS:
            screen = Screen(name=name, screen_type=screen_type, capacity=capacity, is_active=True)
            db.add(screen)
            screens.append(screen)
        await db.flush()
        print(f"  ✓ {len(screens)} screens")

        # ── Seats (rows A-J, 10 seats each = 100 per screen) ─────────
        rows = "ABCDEFGHIJ"
        total_seats = 0
        for i, screen in enumerate(screens):
            for row in rows:
                for num in range(1, 11):
                    db.add(Seat(
                        screen_id=screen.id,
                        row=row,
                        number=num,
                        seat_type=seat_type_for(i, row, num),
                        is_active=True,
                    ))
                    total_seats += 1
        await db.flush()
        print(f"  ✓ {total_seats} seats ({total_seats // len(screens)} per screen)")

        # ── Showtimes ─────────────────────────────────────────────────
        base = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

        for day, hour, minute, screen_idx, movie_idx in SCHEDULE:
            movie = movies[movie_idx]
            start = base + timedelta(days=day, hours=hour, minutes=minute)
            end = start + timedelta(minutes=movie.duration_minutes + 20)  # +20 for trailers
            price_reg, price_vip = PRICES[screen_idx]
            db.add(Showtime(
                movie_id=movie.id,
                screen_id=screens[screen_idx].id,
                start_time=start,
                end_time=end,
                price_regular=price_reg,
                price_vip=price_vip,
                is_active=True,
            ))
        await db.flush()
        print(f"  ✓ {len(SCHEDULE)} showtimes over 7 days")

        await db.commit()

    print("\n✅  Seed complete!\n")
    print("  Test credentials")
    print("  ─────────────────────────────────────────")
    print("  Admin : admin@cinema.com   / Admin1234!")
    print("  User 1: alice@example.com  / Alice1234!")
    print("  User 2: bob@example.com    / Bob12345!")


if __name__ == "__main__":
    asyncio.run(seed())
