from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from api.routers import admin_stats, auth, bookings, movies, payments, showtimes, ws
from core.config import settings
from core.database import AsyncSessionLocal, engine
from core.telemetry import setup_telemetry
from messaging.producer import close as close_rabbitmq


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Shutdown
    await engine.dispose()
    await close_rabbitmq()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Must be called AFTER app is created, BEFORE it starts
setup_telemetry(app, engine, settings.otel_exporter_otlp_endpoint)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_stats.router)
app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(showtimes.router)
app.include_router(bookings.router)
app.include_router(payments.router)
app.include_router(ws.router)


@app.get("/health", tags=["system"])
async def health_check():
    db_status = "ok"
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"error: {exc}"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "version": "0.1.0",
        "services": {"database": db_status},
    }