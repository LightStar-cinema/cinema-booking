# Database Design — CineLuxe

> Written by: **Madirimova Nargiza** — Database Engineer

---

## What is a database?

A database is like a giant **digital filing cabinet**. Imagine a real cinema:
- A folder for **all customers** (their names, emails, phone numbers)
- A folder for **all movies** (titles, posters, genres)
- A folder for **all bookings** (who booked what, when, for how much)

A database keeps all this information organized so the website can find
anything fast, even if there are millions of records.

For CineLuxe, we use **PostgreSQL** — one of the most popular and
reliable databases in the world.

---

## Our 8 tables

Each "table" is like one spreadsheet. Here is what we have:

| Table | What it stores | Example |
|---|---|---|
| `users` | People who use the site | Alice, alice@example.com |
| `movies` | Films we show | Inception, 148 min, PG-13 |
| `screens` | Cinema halls | "IMAX Hall 1", 100 seats |
| `seats` | Every individual seat | Row A, seat 5 in IMAX Hall 1 |
| `showtimes` | When a movie plays | Inception, Friday 7pm, Hall 1 |
| `bookings` | A reservation | Alice booked 2 seats for 7pm |
| `booking_seats` | Exactly which seats | Alice got seats A5 and A6 |
| `payments` | Payment records | Alice paid $20 by card |

---

## Why we need each table (simple stories)

### users
We need to know WHO is booking. Each user has a unique email so we
can identify them and show them their own bookings.

### movies
We need a list of WHAT is showing. The home page reads from this table
to show the "Now Showing" section.

### screens
A cinema has multiple halls. Hall 1 is IMAX (big, expensive).
Hall 2 is Standard (smaller, cheaper). Each hall has its own seats.

### seats
Every seat belongs to one specific hall. Hall 1 has seats A1 to J10.
Hall 2 also has seats A1 to J10 — but they are DIFFERENT seats
because they are in different halls.

### showtimes
A movie can play many times a day. Inception might play at 2pm,
5pm, and 9pm. Each is a separate showtime record.

### bookings
When Alice reserves seats, we create one booking record with:
- Her user ID (who she is)
- The showtime ID (which showing she picked)
- Status: PENDING then CONFIRMED or CANCELLED
- The total price

### booking_seats (the most important table!)
This is a special "junction" table. It answers the question:
"For this booking, which exact seats were reserved?"

One booking can have many seats (Alice booked A5, A6, A7).
One seat can appear in many bookings (different days, different people).
This is called a many-to-many relationship.

### payments
Every booking has one payment. We track how much was paid,
how it was paid (card/cash), and whether it succeeded.

---

## How we stop double-booking (our smartest trick!) 🔒

The problem: Alice and Bob both click seat A5 at the exact same moment.
Who gets it? If we are not careful, BOTH get it — disaster!

We solved it with TWO layers of protection:

**Layer 1 — Redis lock (super fast)**
The moment someone clicks a seat, we put a 30-second lock on it
in Redis (a fast memory store). Anyone else who tries gets blocked
immediately.

**Layer 2 — Database unique constraint (final guard)**
In the booking_seats table we have this rule:
```
UNIQUE(seat_id, showtime_id)
```
This means: the same seat at the same showtime can only exist ONCE
in the table. Even if Redis somehow fails, the database itself
will refuse to save a duplicate. It is impossible to double-book.

This technique is called "defense in depth" — two locks instead of one.

---

## Primary keys and foreign keys explained simply

### Primary key (PK)
Every row in every table has a unique ID, like a fingerprint.
We use UUIDs — long random strings like `7f3e8b4a-9c2d-4e1a-...`
No two rows ever have the same UUID.

### Foreign key (FK)
A foreign key is when one table points to another table.
Example: the bookings table has a column called `user_id`.
This is a foreign key pointing to the users table.
It means: "this booking belongs to THAT user."

---

## How tables are connected

- One user can make many bookings
- One movie can have many showtimes
- One screen can have many seats
- One screen can host many showtimes
- One showtime can have many bookings
- One booking can include many seats (via booking_seats)
- One booking has exactly one payment

---

## We also use two more databases

PostgreSQL is our main database, but for some tasks it is not
the best tool. So we also use:

| Store | What for | Why not PostgreSQL? |
|---|---|---|
| **Redis** | Seat locks, rate limiting | 10x faster (stored in memory), has built-in timers |
| **MongoDB** | Daily report snapshots | Stores flexible data without a strict structure |

Using the right tool for the right job is called **polyglot persistence**.

---

## How anyone can rebuild our database from scratch

We use a tool called **Alembic** for database migrations.
A migration is like a recipe step for the database.

We have 3 migration files:
1. Create the initial 8 tables
2. Add the is_coming_soon column to movies
3. Add extra fields to bookings

To rebuild everything from scratch, run:
```
alembic upgrade head
```

Then to add sample data (movies, seats, users):
```
python scripts/seed.py
```

That is the CineLuxe database — designed and documented by Madirimova Nargiza. 🗄️

