# Frontend Documentation — CineLuxe

> Written by: **Islomova Mushtari** (U2310103) — Frontend Developer

## What is the frontend?

The frontend is everything you SEE in your browser — buttons,
colors, pictures, menus, the seat map. It is the face of the website.

Think of a restaurant:
- Frontend = dining room and menus — what customers see
- Backend = the kitchen — where food is actually prepared

Note: As stated in the project requirements, AI-generated frontend
code is explicitly allowed. We used AI tools to help generate the
HTML/CSS structure, then customized it to match our cinema theme
and connected it to our backend API.

---

## The 8 pages

| Page | File | What it does |
|---|---|---|
| Home | LANDING_PAGE.html | Shows all movies, hero banner |
| Movie Details | MOVIE_DETAILS.html | One movie info and showtimes |
| Seat Selection | SELECT_SEATS.html | Interactive seat map, live updates |
| Checkout | CHECKOUT.html | Payment form |
| My Bookings | MY_BOOKINGS.html | User booking history |
| Admin Panel | ADMIN.html | Manage movies (admin only) |
| Cinemas | CINEMAS.html | Cinema hall information |
| Offers | OFFERS.html | Special deals |

---

## How frontend talks to backend

The frontend asks the backend for all data using the API.

Example — loading movies on home page:
```javascript
fetch("/api/movies")
  .then(response => response.json())
  .then(movies => {
    // draw each movie poster on the page
  });
```

Frontend calls backend: "give me movies."
Backend replies with JSON data.
Frontend draws it on screen.

---

## Real-time seat updates (WebSocket)

Normal HTTP: browser asks server "any updates?" every few seconds.
WebSocket: server PUSHES updates to browser the moment anything changes.

So if Bob books seat A5 while Alice is viewing the seat map,
Alice sees A5 turn gray INSTANTLY — no page refresh needed.

---

## Design theme — Cinematic Noir

| Color | Code | Used for |
|---|---|---|
| Pure black | #0a0a0a | Page background |
| Dark gray | #1a1a1a | Cards and forms |
| Cinema red | #e50914 | Buttons and highlights |
| Off-white | #f5f5f5 | All text |
| Green | #22c55e | Available seats |
| Gray | #6b7280 | Booked seats |
| Yellow | #fbbf24 | Selected seats |

Fonts: Bebas Neue (titles) + Inter (body text)

---

Frontend documented by Islomova Mushtari (U2310103).
