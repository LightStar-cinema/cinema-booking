# Cinema Ticket Booking System

A production-grade cinema seat reservation API built as a university project to demonstrate
distributed-systems design patterns from _Designing Data-Intensive Applications_ (Kleppmann).

## Tech Stack

| Layer | Technology |
|---|---|
| API | Python 3.12 · FastAPI 0.111 · Uvicorn |
| Primary DB | PostgreSQL 16 (SQLAlchemy 2 async · Alembic) |
| Cache / Locks | Redis 7 (token-bucket rate limiter · seat-reservation locks) |
| Document store | MongoDB 7 (daily batch reports) |
| Message broker | RabbitMQ 3.13 (booking confirmation events) |
| Real-time | WebSockets (per-showtime seat availability broadcast) |
| Observability | OpenTelemetry → Prometheus · Grafana · Loki |
| Gateway | Nginx 1.27 |
| Runtime | Docker Compose |

---

## Architecture

```
Browser / Client
       │
  ┌────▼────┐
  │  Nginx  │  :80   reverse-proxy + WebSocket upgrade
  └────┬────┘
       │
  ┌────▼────────────────────────────────────────────┐
  │  FastAPI API  (cinema_api)                       │
  │                                                  │
  │  /api/auth        JWT register · login · me      │
  │  /api/movies      CRUD (admin-gated)             │
  │  /api/showtimes   listing · seat availability    │
  │  /api/bookings    reserve seats (Redis lock)     │
  │  /api/payments    process · confirm              │
  │  /ws/showtimes/{id}  real-time seat events       │
  └────┬──────────┬──────────┬──────────┬───────────┘
       │          │          │          │
  ┌────▼─┐  ┌────▼──┐  ┌───▼───┐  ┌──▼──────┐
  │  PG  │  │ Redis │  │ Mongo │  │RabbitMQ │
  └──────┘  └───────┘  └───────┘  └────┬────┘
                                        │
                              ┌─────────▼──────────┐
                              │ notification_worker │  simulates email
                              └────────────────────┘
                              ┌────────────────────┐
                              │  daily_report       │  midnight → Mongo
                              └────────────────────┘

Telemetry (all signals via OTLP):
  API → otel-collector → Prometheus → Grafana
                      → Loki       → Grafana
```

---

## Quick Start

### Prerequisites

- Docker Desktop 4.x (Engine ≥ 24, Compose ≥ 2.24)
- 4 GB RAM available to Docker

### One-command setup

```bash
# 1. Copy the environment template
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux

# 2. Build images and start everything
docker compose up -d --build

# 3. Apply database migrations (first run only)
docker compose exec api alembic upgrade head

# 4. Verify all containers are healthy
docker compose ps
```

Everything is now running. See [Service URLs](#service-urls) below.

---

## Environment Variables

Copy `.env.example` to `.env` and edit before first run.
**Never commit `.env` to version control.**

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_DB` | `cinema` | PostgreSQL database name |
| `POSTGRES_USER` | `cinema_user` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `cinema_pass` | PostgreSQL password — **change in production** |
| `REDIS_PASSWORD` | `redis_pass` | Redis AUTH password |
| `MONGO_USER` | `mongo_user` | MongoDB root username |
| `MONGO_PASSWORD` | `mongo_pass` | MongoDB root password |
| `MONGO_DB` | `cinema_logs` | MongoDB database for batch reports |
| `RABBITMQ_USER` | `rabbit_user` | RabbitMQ username |
| `RABBITMQ_PASSWORD` | `rabbit_pass` | RabbitMQ password |
| `RABBITMQ_VHOST` | `cinema` | RabbitMQ virtual host |
| `SECRET_KEY` | `change-me-in-production` | JWT signing secret — **must change** |
| `DEBUG` | `true` | SQLAlchemy echo / verbose logging |
| `GRAFANA_PASSWORD` | `admin` | Grafana admin password |

---

## Service URLs

| Service | URL | Credentials |
|---|---|---|
| **Swagger UI** | http://localhost/api/docs | — (use Register → Login) |
| **ReDoc** | http://localhost/api/redoc | — |
| **Grafana** | http://localhost:3000 | admin / `$GRAFANA_PASSWORD` |
| **Prometheus** | http://localhost:9090 | — |
| **RabbitMQ UI** | http://localhost:15672 | `$RABBITMQ_USER` / `$RABBITMQ_PASSWORD` |
| **Health check** | http://localhost/health | — |

---

## API Overview

### Authentication

```
POST /api/auth/register   { email, password, full_name }  → JWT token
POST /api/auth/login      form: username, password        → JWT token
GET  /api/auth/me                                         → user profile
```

All protected endpoints require `Authorization: Bearer <token>`.

### Movies (public read · admin write)

```
GET    /api/movies               ?genre=&active_only=true&skip=&limit=
GET    /api/movies/{id}
POST   /api/movies               (admin)
PATCH  /api/movies/{id}          (admin)
DELETE /api/movies/{id}          (admin, soft-delete)
```

### Showtimes

```
GET  /api/showtimes              ?movie_id=&date=YYYY-MM-DD
GET  /api/showtimes/{id}         → showtime + per-seat availability
POST /api/showtimes              (admin)
```

### Bookings

```
POST /api/bookings               { showtime_id, seat_ids[] }
GET  /api/bookings/me
GET  /api/bookings/{id}
POST /api/bookings/{id}/cancel
```

`POST /api/bookings` uses a two-layer double-booking guard:

1. **Redis Lua lock** — atomic all-or-nothing seat reservation (30 s TTL)
2. **PostgreSQL unique constraint** — `(seat_id, showtime_id)` on `booking_seats`

Rate-limited to **5 attempts per user per 60 s** (token-bucket, Redis-backed).

### Payments

```
POST /api/payments    { booking_id, payment_method }  → payment record
GET  /api/payments/{id}
```

Triggers a `booking_confirmed` event on RabbitMQ and confirms the booking.

### WebSocket — Real-time Seat Availability

```
WS  /ws/showtimes/{showtime_id}
```

Connect, then receive push events as seats change state:

```jsonc
// On connect
{ "event": "connected", "showtime_id": "...", "viewers": 3 }

// When a booking attempt starts
{ "event": "seat_status", "seats": [{ "seat_id": "...", "status": "locked" }] }

// When payment completes
{ "event": "seat_status", "seats": [{ "seat_id": "...", "status": "booked" }] }

// When booking is cancelled
{ "event": "seat_status", "seats": [{ "seat_id": "...", "status": "available" }] }
```

Call `GET /api/showtimes/{id}` first for the initial snapshot, then connect the socket for deltas.

---

## Database Migrations (Alembic)

```bash
# Apply all pending migrations
docker compose exec api alembic upgrade head

# Generate a new migration from model changes
docker compose exec api alembic revision --autogenerate -m "describe the change"

# Rollback one step
docker compose exec api alembic downgrade -1

# Show migration history
docker compose exec api alembic history --verbose
```

---

## Background Workers

Both workers share the same Docker image as the API and are started automatically by Compose.

### Notification Worker

Consumes `booking.confirmed` events from RabbitMQ and simulates sending confirmation emails.

```bash
# View live logs
docker compose logs -f notification_worker

# Run interactively (bypasses Compose restart policy)
docker compose run --rm notification_worker python -m workers.notification_worker
```

### Daily Report Worker

Wakes at UTC midnight, aggregates the day's confirmed bookings from PostgreSQL, and writes
a summary document to the MongoDB `daily_reports` collection.

```bash
# Run immediately for yesterday
docker compose exec daily_report_worker python -m workers.daily_report --now

# Run for a specific date
docker compose exec daily_report_worker python -m workers.daily_report --date 2025-05-09

# View scheduled runs
docker compose logs -f daily_report_worker
```

---

## Observability

All telemetry is collected via the OpenTelemetry Collector and visualised in Grafana.

| Signal | Flow |
|---|---|
| Traces | API → OTLP gRPC → otel-collector → stdout |
| Metrics | API → OTLP gRPC → otel-collector → Prometheus `:8889` → Grafana |
| Logs | API → OTLP gRPC → otel-collector → Loki → Grafana |

Open **Grafana** at http://localhost:3000 and navigate to **Dashboards → Cinema API — Overview**.

Key panels:

- **Requests/s** — live request rate by route
- **Error Rate %** — 4xx + 5xx as a percentage of all requests
- **Booking Rate** — `cinema_bookings_created_total` custom counter (5 m rolling)
- **p50 / p95 / p99 latency** — from the `http_server_request_duration_seconds` histogram
- **Application Logs** — streaming from Loki, label `{job="cinema-api"}`

---

## Rate Limiting

Two routes are protected by a **token-bucket** rate limiter built from scratch (no external
rate-limit libraries), backed by Redis Lua scripts for atomic read-modify-write:

| Endpoint | Strategy | Limit |
|---|---|---|
| `POST /api/bookings` | per authenticated user ID | 5 req / 60 s |
| `POST /api/auth/register` | per client IP | 3 req / 60 s |

When the limit is hit the API returns **HTTP 429** with `Retry-After` and `X-RateLimit-*` headers.

---

## Project Layout

```
.
├── app/
│   ├── api/
│   │   ├── deps.py                  shared FastAPI dependencies
│   │   └── routers/                 auth · movies · showtimes · bookings · payments · ws
│   ├── components/
│   │   └── rate_limiter.py          token-bucket (Redis Lua, from scratch)
│   ├── core/
│   │   ├── config.py                Pydantic settings from .env
│   │   ├── database.py              async SQLAlchemy engine + session factory
│   │   └── telemetry.py             OpenTelemetry traces · metrics · logs
│   ├── messaging/
│   │   ├── producer.py              RabbitMQ async publisher (aio-pika)
│   │   └── schemas.py               Pydantic event schemas
│   ├── models/                      SQLAlchemy 2 ORM models
│   ├── schemas/                     Pydantic request/response schemas
│   ├── workers/
│   │   ├── notification_worker.py   RabbitMQ consumer → simulated email
│   │   └── daily_report.py          midnight batch job → MongoDB
│   ├── alembic/                     migration env + versions
│   ├── main.py                      FastAPI app · lifespan · CORS
│   └── requirements.txt
├── nginx/nginx.conf                 gateway config (REST + WebSocket)
├── observability/
│   ├── otel-collector.yaml          OTLP → Prometheus + Loki pipelines
│   ├── prometheus.yml               scrape config
│   ├── loki-config.yml              single-node Loki config
│   └── grafana/provisioning/        auto-provisioned datasources + dashboard
├── postgres/init/01-init.sql        schema seed hook
├── docker-compose.yml               12 services
└── .env.example                     environment variable template
```

---

## Contributing

1. **Branch** — create a feature branch from `main`.
2. **Migrations** — if you change any SQLAlchemy model, generate a migration:
   ```bash
   docker compose exec api alembic revision --autogenerate -m "short description"
   ```
3. **Style** — the project uses no linter config yet; follow PEP 8 and the patterns
   already in place (type annotations, `Annotated` deps, no docstring blocks).
4. **No half-finished features** — every PR should leave the system runnable end-to-end.
5. **Environment** — never add secrets to source files; always use `.env` variables.

---

## License

MIT — free to use for educational purposes.


## Changelog

### v1.0.0 — 2026-05-10
- Initial release: full cinema ticket booking system
- PostgreSQL + Alembic migrations (R3)
- FastAPI REST API with Swagger UI (R4)
- MongoDB document store for batch reports (R5)
- Redis caching, seat locks, token-bucket rate limiter (R6, R11)
- WebSocket real-time seat availability (R7)
- Nginx API gateway (R8)
- Docker Compose orchestration — 12 services (R9)
- RabbitMQ notification pipeline + daily report worker (R10)
- OpenTelemetry → Prometheus + Grafana + Loki (R12)

- <!-- Reviewed by Ergasheva Fotima - report writer 1 -->
