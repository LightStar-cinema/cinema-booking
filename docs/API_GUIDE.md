# API Guide — CineLuxe

> Written by: **Ergasheva Fotima** — API Documentation

---

## What is an API?

An API (Application Programming Interface) is a way for two programs
to talk to each other.

Think of a restaurant:
- The **menu** is the API — it lists what you can order
- The **waiter** takes your request to the kitchen
- The **kitchen** sends back food

In CineLuxe, the **frontend** (the website you see in your browser) is
the customer. The **backend** (Python/FastAPI server) is the kitchen.
The API is the menu — it lists everything you can ask for.

---

## How one API call works (a real example)

When you open the home page and see movies, here is what happened:

1. Your browser asked: `GET /api/movies`
2. The backend found all movies in the database
3. The backend replied with a JSON list (text format)
4. JavaScript drew the movie posters from that list

It is like sending a text message and getting a reply. Simple!

---

## All 18 endpoints (the complete menu)

### Authentication — Who are you?

| Method | URL | What it does | Who can use it |
|---|---|---|---|
| POST | `/api/auth/register` | Create a new account | Anyone |
| POST | `/api/auth/login` | Sign in, get a token | Anyone |
| GET | `/api/auth/me` | See my own profile | Logged-in users |

### Movies

| Method | URL | What it does | Who can use it |
|---|---|---|---|
| GET | `/api/movies` | List all movies | Anyone |
| GET | `/api/movies/{id}` | One movie's details | Anyone |
| POST | `/api/movies` | Add a new movie | Admin only |
| PATCH | `/api/movies/{id}` | Edit a movie | Admin only |
| DELETE | `/api/movies/{id}` | Remove a movie | Admin only |

### Showtimes

| Method | URL | What it does | Who can use it |
|---|---|---|---|
| GET | `/api/showtimes` | List showtimes | Anyone |
| GET | `/api/showtimes/{id}` | One showtime + seat map | Anyone |
| POST | `/api/showtimes` | Create a showtime | Admin only |

### Bookings

| Method | URL | What it does | Who can use it |
|---|---|---|---|
| POST | `/api/bookings` | Reserve seats | Logged-in users |
| GET | `/api/bookings/me` | My booking history | Logged-in users |
| GET | `/api/bookings/{id}` | One booking's details | Owner only |
| POST | `/api/bookings/{id}/cancel` | Cancel a booking | Owner only |

### Payments

| Method | URL | What it does | Who can use it |
|---|---|---|---|
| POST | `/api/payments` | Pay for a booking | Logged-in users |
| GET | `/api/payments/{id}` | Payment details | Owner only |

### Admin

| Method | URL | What it does | Who can use it |
|---|---|---|---|
| GET | `/api/admin/stats/weekly` | Revenue and tickets sold | Admin only |

---

## The 4 verbs — what each one means

Every request uses one of these action words:

| Verb | Means | Like saying... |
|---|---|---|
| **GET** | Give me information | "Show me the menu" |
| **POST** | Create something new | "I want to order this" |
| **PATCH** | Update something | "Change my order please" |
| **DELETE** | Remove something | "Cancel that order" |

---

## A full booking example — step by step

Alice wants to book seat A5 for Inception at 7pm.
Here is the full conversation between frontend and backend:

### Step 1 — Alice logs in
```
POST /api/auth/login
Send: { "username": "alice@example.com", "password": "Alice1234!" }
```
Backend replies:
```json
{ "access_token": "eyJhbGc...xyz", "token_type": "bearer" }
```
This token is like a wristband at a concert. Alice keeps it and
sends it with every future request to prove who she is.

### Step 2 — Alice looks at movies
```
GET /api/movies
```
Backend replies with a list of movies including Inception.

### Step 3 — Alice picks a showtime
```
GET /api/showtimes/abc-123
```
Backend replies with showtime details and which seats are free.

### Step 4 — Alice books seat A5
```
POST /api/bookings
Send token + body: { "showtime_id": "abc-123", "seat_ids": ["seat-A5"] }
```
Backend replies:
```json
{
  "id": "booking-789",
  "status": "PENDING",
  "total_amount": 15.00,
  "booking_reference": "CN-X7Y9Z2"
}
```
Status is PENDING because Alice has not paid yet.

### Step 5 — Alice pays
```
POST /api/payments
Send token + body: { "booking_id": "booking-789", "payment_method": "CARD" }
```
Backend replies:
```json
{ "status": "COMPLETED", "transaction_id": "TXN-12345" }
```
Booking is now CONFIRMED. Alice has her seat! ✅

---

## Error codes — what happens when things go wrong

When something fails, the API sends a number called a status code:

| Code | Meaning | Example |
|---|---|---|
| 200 | OK — everything worked | Login successful |
| 201 | Created — new thing was made | Booking created |
| 400 | Bad request — you sent wrong data | Missing email field |
| 401 | Not logged in — token missing | Forgot to send token |
| 403 | Forbidden — not allowed | Regular user tried admin action |
| 404 | Not found — does not exist | Movie ID is wrong |
| 409 | Conflict — collision | Someone just booked that seat! |
| 429 | Too many requests — slow down | Rate limiter blocked you |
| 500 | Server error — our mistake | Something crashed |

---

## How login tokens work (JWT)

When you log in, the backend gives you a JWT token.
It looks like this:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhYmMtMTIzIn0.xyz
```

It is like a signed letter from the backend that says:
"I confirm this is Alice, logged in at 3pm, valid until 3pm tomorrow."

You send this token in every request:
```
Authorization: Bearer eyJhbGc...xyz
```

The backend checks the signature. If it is valid, you are allowed in.
Tokens expire after **24 hours** — then you log in again.

---

## Rate limiting — no spamming allowed

If someone tries to make 1000 bookings per second:
- After 5 attempts in 60 seconds → API replies with **429 Too Many Requests**
- The reply includes a `Retry-After` header saying how many seconds to wait

This protects our server from attacks.

---

## Try the API yourself!

Open this in your browser:
**http://138.68.76.246/api/docs**

This is Swagger UI — an interactive page where you can:
- See all 18 endpoints
- Click any endpoint
- Fill in a form
- Click "Execute" to test it live

No coding needed. It is like a control panel for the API.

---

API documentation written by Ergasheva Fotima.
