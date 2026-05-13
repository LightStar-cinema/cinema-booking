"""
OpenTelemetry setup — all three signals wired for the Cinema API.

Signal flows
────────────
  Traces   FastAPI/SQLAlchemy auto-instrumentation
             → OTLP gRPC → otel-collector → debug (stdout)
  Metrics  FastAPIInstrumentor + custom counters
             → OTLP gRPC → otel-collector → Prometheus scrape :8889
  Logs     Python logging bridge → OTel LoggerProvider
             → OTLP gRPC → otel-collector → Loki

Metric names (as seen in Prometheus after otel-collector transforms them)
─────────────────────────────────────────────────────────────────────────
  http_server_request_duration_seconds_{bucket,count,sum}
      Histogram from FastAPIInstrumentor.
      Labels: http_route, http_request_method, http_response_status_code

  http_server_active_requests
      UpDownCounter from FastAPIInstrumentor.

  cinema_bookings_created_total
      Custom counter incremented in bookings router on successful commit.

Lua / Redis note: this module has no Redis dependency — only OTel SDK.
"""

import logging

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_SERVICE_NAME = "cinema-api"
_SERVICE_VERSION = "0.1.0"

# ── Public instruments ────────────────────────────────────────────────────────
# Set to real Counter objects during setup_telemetry().
# Routers check `if telemetry.<counter>:` before calling .add() so they are
# safe to import even before the lifespan initialises telemetry.

bookings_created: metrics.Counter | None = None
payments_processed: metrics.Counter | None = None


# ── Setup ─────────────────────────────────────────────────────────────────────

def setup_telemetry(app, engine, otlp_endpoint: str) -> None:
    """
    Initialise all three OTel signals and wire auto-instrumentation.
    Must be called once during the FastAPI lifespan startup, after the app
    object is fully constructed (so FastAPIInstrumentor can wrap it).
    """
    global bookings_created, payments_processed

    resource = Resource.create({
        "service.name":    _SERVICE_NAME,
        "service.version": _SERVICE_VERSION,
    })

    # ── Traces ───────────────────────────────────────────────────────────────
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        )
    )
    trace.set_tracer_provider(tracer_provider)

    # ── Metrics ──────────────────────────────────────────────────────────────
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True),
        export_interval_millis=15_000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    meter = metrics.get_meter(_SERVICE_NAME, _SERVICE_VERSION)

    bookings_created = meter.create_counter(
        name="cinema.bookings.created",
        unit="1",
        description="Number of bookings successfully committed to the database",
    )
    payments_processed = meter.create_counter(
        name="cinema.payments.processed",
        unit="1",
        description="Number of payment transactions processed (by status)",
    )

    # ── Logs ─────────────────────────────────────────────────────────────────
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(endpoint=otlp_endpoint, insecure=True)
        )
    )
    set_logger_provider(logger_provider)

    # Bridge Python's standard `logging` → OTel logger provider → otel-collector → Loki.
    # Only root logger; noisy third-party loggers can be excluded by name.
    otel_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    logging.getLogger().addHandler(otel_handler)

    # Inject trace_id / span_id into every log record so Loki log lines are
    # correlated with the corresponding trace in future when Tempo is added.
    LoggingInstrumentor().instrument(set_logging_format=True)

    # ── Auto-instrumentation ─────────────────────────────────────────────────
    # FastAPIInstrumentor creates http.server.request.duration histogram and
    # http.server.active_requests updowncounter automatically for every route.
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=tracer_provider,
        meter_provider=meter_provider,
    )

    # SQLAlchemy: creates db.client.operation.duration histogram per query.
    # engine.sync_engine is the underlying synchronous Engine inside AsyncEngine.
    SQLAlchemyInstrumentor().instrument(
        engine=engine.sync_engine,
        tracer_provider=tracer_provider,
    )

    logging.getLogger(__name__).info(
        "OpenTelemetry initialised — endpoint=%s service=%s",
        otlp_endpoint,
        _SERVICE_NAME,
    )
