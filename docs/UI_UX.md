# UI/UX Design Guide — CineLuxe

> Written by: **Minajev Salamat** — UI/UX Designer

---

## What is UI/UX?

**UI** (User Interface) = how the website LOOKS
— the colors, fonts, buttons, and layout.

**UX** (User Experience) = how the website FEELS to use
— is it easy? Is it fast? Is it enjoyable?

A good UI without good UX is like a beautiful door that is hard to open.
A good UX without good UI is like a comfortable chair that looks terrible.
You need both.

Our design goal for CineLuxe:
**Make booking a movie ticket feel as fun as actually watching one.**

---

## The "Cinematic Noir" theme

We did not want CineLuxe to look like a boring form website.
We wanted it to feel like a real cinema — dark, dramatic, exciting.

So we chose the **Cinematic Noir** style:
- Very dark background (like sitting in a cinema theater)
- Bright red accent color (like classic cinema curtains)
- Big bold movie posters that jump off the dark background
- Clean layouts with lots of empty space

This same style is used by Netflix, IMDb, and most cinema apps because:
- Dark backgrounds feel like a real movie theater
- Movie posters look much more vibrant on dark backgrounds
- Less eye strain when people browse at night

---

## Color palette

| Color name | Code | Where it is used |
|---|---|---|
| Pure black | `#0a0a0a` | Main page background |
| Dark gray | `#1a1a1a` | Cards (movie posters, forms) |
| Cinema red | `#e50914` | Buttons, links, highlights |
| Off-white | `#f5f5f5` | All body text |
| Muted gray | `#888888` | Secondary text (dates, labels) |
| Success green | `#22c55e` | Available seats on seat map |
| Selection yellow | `#fbbf24` | Seats you have selected |
| Booked red | `#dc2626` | Seats already taken |

---

## Fonts

| Font | Where | Why |
|---|---|---|
| **Inter** | Body text, buttons | Clean and modern, easy to read |
| **Bebas Neue** | Big titles, movie names | Bold and dramatic, like real movie posters |

Font sizes we use:
- 12px — tiny labels
- 16px — normal text
- 20px — small headings
- 32px — page titles
- 48px+ — hero text on landing page

---

## The 8 pages and design choices

### 1. Landing page (LANDING_PAGE.html)
The home page — first impression matters.
- Big hero banner with featured movie fills the whole screen
- Horizontal row of movie poster cards below (like Netflix)
- "Coming Soon" section builds excitement for future films

### 2. Movie details (MOVIE_DETAILS.html)
- Large poster on the left side
- Showtime buttons (3pm, 7pm, 9pm) are clear and easy to tap
- Description and cast below the important stuff

### 3. Seat selection (SELECT_SEATS.html)
The most important page — must be very clear.
- Visual grid that looks like a real cinema hall
- Screen shown at the top so users know which way is "front"
- Color codes: green = free, gray = taken, yellow = your selection
- Updates in real time — if someone else books a seat it turns gray instantly

### 4. Checkout (CHECKOUT.html)
- Order summary always visible on the right
- Simple card form on the left — no clutter
- Big bright red "Pay Now" button — impossible to miss

### 5. My Bookings (MY_BOOKINGS.html)
- Each booking is one big card with the movie poster
- Status shown as a colored badge (green = confirmed, gray = cancelled)
- Cancel button only appears when the booking can still be cancelled

### 6. Admin panel (ADMIN.html)
- Sidebar navigation for quick access
- Tables for managing movies — admins want efficiency, not decoration
- Stats cards at the top showing revenue and tickets sold

### 7. Cinemas (CINEMAS.html)
- Information about each cinema hall
- Shows screen type (IMAX, Standard, 3D, Dolby)

### 8. Offers (OFFERS.html)
- Special deals and student discounts
- Bright cards to make offers stand out

---

## Small details that make a big difference

**Hover effects**
Movie cards lift up slightly when you point at them. Makes the site
feel alive and interactive.

**Loading states**
When the page is waiting for data from the server, a spinner shows.
Users know something is happening — they will not think it is broken.

**Confirmation before cancel**
Before cancelling a booking, a popup asks "Are you sure?"
Protects users from accidental clicks.

**Error messages in plain English**
Instead of "ERR_DB_CONFLICT_409" we show:
"Sorry, that seat was just booked by someone else. Please choose another."

**Disabled buttons stay visible**
If "Pay" is not ready yet (form not filled), the button is gray but
still visible. Users know what step is next.

---

## Mobile friendly design

About half of all bookings happen on phones.
Every page works on:
- Phones (from 320px wide)
- Tablets (768px wide)
- Laptops (1024px wide)
- Big monitors (1440px wide)

On phones the seat map rows scroll sideways, buttons get bigger for
easy tapping, and columns stack vertically.

---

## Spacing rules (the secret to looking professional)

Every margin and gap in our design is a multiple of 4 pixels:
4, 8, 12, 16, 24, 32, 48, 64...

This sounds simple but it is the difference between looking like a
cheap website and looking like a professional product. Consistent
spacing makes everything feel calm and organized.

---

## Accessibility — everyone deserves to book a movie

Some users have visual or physical difficulties. We tried to support them:

- High contrast (white text on black background) — easy to read
- Buttons are at least 44x44 pixels — easy to tap on touchscreens
- You can use the site with only a keyboard — no mouse needed
- Images have descriptions for screen reader users

---

UI/UX design by Minajev Salamat. 
