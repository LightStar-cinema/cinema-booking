
# Backend Architecture — CineLuxe

> Written by: **Hazratov Sardorbek** (U2310090) — Tech Lead / Backend Developer

---

## What is the backend?

The backend is the invisible engine of the website. It does all the real work:
- Saves users when they register
- Checks passwords when they log in
- Stores bookings in the database
- Locks seats so two people cannot book the same one at the same time
- Processes payments
- Sends confirmation messages

Think of a cinema:
- Frontend = the lobby (what customers see)
- Backend = the staff offices and kitchen (where everything actually happens)

---

## Technology choices

We built the backend with **Python 3.12** and **FastAPI**.

Why FastAPI?
- One of the fastest Python frameworks
- Automatically generates Swagger documentation
- Validates incoming data automatically
- Built-in support for async operations (handles many requests at once)

---

## How the backend connects to everything

```
Browser (frontend)
      ↓ HTTP request
   Nginx (port 80)
      ↓
   FastAPI (port 8000)
      ↓           ↓           ↓           ↓
PostgreSQL      Redis       MongoDB    RabbitMQ
(bookings)    (locks)     (reports)  (messages)
```

---

## The booking flow (most important part)

When a user books seats, here is exactly what happens:

1. Frontend sends: POST /api/bookings with seat IDs and showtime ID
2. Backend checks JWT token (is user logged in?)
3. Backend checks rate limiter (is user spamming?)
4. Backend runs Redis Lua script to lock all seats atomically
5. If any seat is already locked → return 409 error immediately
6. Backend creates PENDING booking in PostgreSQL
7. Backend returns booking reference to frontend
8. User pays → backend updates booking to CONFIRMED
9. Backend publishes booking.confirmed event to RabbitMQ
10. notification_worker picks up the message and logs a confirmation email

---

## Double-booking prevention (the hardest problem)

The problem: Alice and Bob click seat A5 at the exact same millisecond.
Without protection, both would get the seat. That is a disaster.

Our solution uses two layers:

**Layer 1 — Redis lock (speed)**
The moment someone clicks a seat, a Lua script atomically:
- Checks if the seat is locked
- If not locked: sets a 30-second lock
- If already locked: returns error immediately
This all happens in ONE atomic operation. No race condition possible.

**Layer 2 — Database constraint (safety)**
In booking_seats table: UNIQUE(seat_id, showtime_id)
Even if Redis somehow failed, PostgreSQL would reject the duplicate.
This is called defense in depth.

---

## From-scratch component (R11)

We built a token-bucket rate limiter from scratch using Redis Lua scripts.
Based on the algorithm in Kleppmann's "Designing Data-Intensive Applications".

Applied to:
- POST /api/bookings: 5 requests per user per 60 seconds
- POST /api/auth/register: 3 requests per IP per 60 seconds

When exceeded: HTTP 429 with Retry-After header.

---

## File structure

```
app/
├── api/routers/     ← All API endpoints (auth, movies, bookings, payments)
├── components/      ← rate_limiter.py (built from scratch)
├── core/            ← config, database setup, telemetry
├── messaging/       ← RabbitMQ publisher
├── models/          ← 8 database table definitions
├── schemas/         ← Request/response data validation
├── workers/         ← notification_worker, daily_report_worker
├── alembic/         ← Database migration files
├── scripts/         ← seed.py (sample data)
└── main.py          ← Application entry point
```

