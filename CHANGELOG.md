# Changelog

All notable changes to the Cinema Ticket Booking System are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.0.0] — 2026-05-10

Initial release — complete end-to-end cinema ticket booking platform.

### Added

#### Infrastructure
- **Docker Compose** stack with 12 services: PostgreSQL 16, Redis 7, MongoDB 7,
  RabbitMQ 3.13, FastAPI, Nginx, OpenTelemetry Collector, Prometheus, Loki,
  Grafana, notification worker, daily-report worker.
- **Nginx** gateway with reverse-proxy for REST (`/api/*`) and WebSocket (`/ws/*`) traffic.
- Environment-variable-driven configuration via `.env` / Pydantic `Settings`.

#### Data Layer
- **PostgreSQL schema** with seven tables: `users`, `movies`, `screens`, `seats`,
  `showtimes`, `bookings`, `booking_seats`, `payments`.
  - `UNIQUE(seat_id, showtime_id)` on `booking_seats` as the hard double-booking guard.
  - `UNIQUE(screen_id, start_time)` on `showtimes` prevents scheduling conflicts.
  - Timestamps (`created_at`, `updated_at`) on all primary entities.
- **Alembic** migration setup with async-compatible `env.py`; `.env` is the single
  source of truth for the database URL.
- **MongoDB** collection `daily_reports` for batch aggregation output.

#### API (FastAPI)
- `POST /api/auth/register` — bcrypt password hashing, JWT (HS256, 24 h expiry).
- `POST /api/auth/login` — OAuth2PasswordRequestForm, Swagger UI compatible.
- `GET  /api/auth/me` — returns authenticated user profile.
- Full movies CRUD (`GET`, `POST`, `PATCH`, `DELETE`); write operations admin-gated.
- Showtimes listing with date and movie filters; `GET /api/showtimes/{id}` returns
  per-seat availability by querying non-cancelled `booking_seats`.
- `POST /api/bookings` — full seat reservation flow (see Concurrency section).
- `GET  /api/bookings/me`, `GET /api/bookings/{id}`, `POST /api/bookings/{id}/cancel`.
- `POST /api/payments` — simulated gateway, confirms booking, triggers RabbitMQ event.
- `GET  /api/payments/{id}`.
- `GET  /health` — database liveness check.
- Auto-generated OpenAPI docs at `/api/docs` (Swagger) and `/api/redoc`.

#### Concurrency — Seat Reservation
- **Redis Lua seat lock** (`_LOCK_SCRIPT`): atomically checks and sets all requested
  seat keys in one round-trip (no interleaving possible). Lock TTL = 30 s.
- **Broadcast state machine**: `locked` → `booked` (on commit) or `available` (on any
  failure). The `finally` block in `create_booking` guarantees the lock is always
  released and the correct WebSocket event is always broadcast.
- PostgreSQL unique constraint on `(seat_id, showtime_id)` is the final hard guarantee
  against any race that slips past the Redis lock.

#### Real-time WebSocket
- `GET /ws/showtimes/{showtime_id}` — per-showtime room managed by `ConnectionManager`
  singleton.
- Three event types: `connected`, `seat_status` (`locked`/`booked`/`available`), `pong`.
- Dead connections pruned silently during every `broadcast()` call.
- Client pattern: fetch initial snapshot via REST, then apply WebSocket deltas.

#### Rate Limiter (from scratch)
- **Token-bucket algorithm** implemented in pure Python with no external rate-limit
  library (`components/rate_limiter.py`).
- Redis Lua script handles all read-modify-write atomically; TTL = 2 × window so idle
  buckets are collected automatically.
- Lua 5.1 safety: uses `math.floor(x) + 1` instead of `math.ceil` to avoid float
  truncation edge cases; TTL passed as pre-computed integer from Python.
- `limit_by_user()` and `limit_by_ip()` dependency factories; stable function-object
  references created at module import so FastAPI deduplicates sub-dependencies correctly.
- Applied: `POST /api/bookings` → 5 / 60 s per user; `POST /api/auth/register` → 3 / 60 s per IP.
- HTTP 429 response includes `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Window`,
  `X-RateLimit-Remaining` headers.

#### Messaging Pipeline (RabbitMQ)
- Topic exchange `cinema`, durable queue `booking.confirmed`, persistent message delivery.
- **Producer** (`messaging/producer.py`): single `RobustConnection` singleton shared
  across requests; publishes **after** `db.commit()` so the DB is always the source of
  truth; errors are logged and swallowed — RabbitMQ outage never rolls back a payment.
- **`BookingConfirmedEvent`** Pydantic schema with full booking details (movie, screen,
  seats, transaction ID, timestamps).
- **`notification_worker`**: consumes events, simulates a structured confirmation email
  via structured logging; `process(requeue=True)` so transient failures retry.
- **`daily_report`**: aggregates PostgreSQL confirmed bookings (totals, revenue, per-movie
  breakdown, cancellations, new users) at UTC midnight; upserts to MongoDB
  `daily_reports` by `report_date` (idempotent re-runs); `--now` and `--date` flags
  for ad-hoc backfills.
- Both workers share the API Docker image; Compose overrides `command`.

#### Observability (OpenTelemetry)
- `core/telemetry.py`: single `setup_telemetry(app, engine, endpoint)` call wires all
  three signals before the first request (called before `lifespan` yield).
- **Traces**: `TracerProvider` + `BatchSpanProcessor` + `OTLPSpanExporter`; FastAPI and
  SQLAlchemy auto-instrumented.
- **Metrics**: `MeterProvider` + `PeriodicExportingMetricReader` (15 s) + `OTLPMetricExporter`;
  custom counters `cinema.bookings.created` and `cinema.payments.processed`.
- **Logs**: Python `logging` bridged to OTel `LoggerProvider` via `LoggingHandler`;
  `LoggingInstrumentor` injects `trace_id`/`span_id` into every record for future
  Tempo correlation.
- otel-collector routes metrics → Prometheus scrape endpoint `:8889`; logs → Loki.
- **Grafana dashboard** (`cinema_overview.json`) auto-provisioned with 9 panels:
  four stat cards (RPS, active requests, bookings, error %), two time-series
  (RPS by route, error breakdown), booking rate, p50/p95/p99 latency, application logs.

### Architecture decisions

| Decision | Rationale |
|---|---|
| Async SQLAlchemy + asyncpg | Non-blocking DB calls; no thread-pool overhead |
| UUID primary keys | No sequence contention under concurrent inserts |
| Price snapshotted in `booking_seats` | Price changes never retroactively affect bookings |
| Lua scripts for both rate limiter and seat lock | Single round-trip atomicity; no WATCH/MULTI/EXEC retry loop |
| Publish event after `db.commit()` | DB is source of truth; no phantom events on rollback |
| Upsert in daily report | Safe to re-run the job for the same date without duplicates |
| Module-level rate-limiter dep references | FastAPI uses function-object identity for dep caching |
| `engine.sync_engine` for SQLAlchemy instrumentation | OTel instrumentor hooks sync events which async wraps |

---

[1.0.0]: https://github.com/your-org/cinema-booking/releases/tag/v1.0.0
