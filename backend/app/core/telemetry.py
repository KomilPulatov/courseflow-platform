"""OpenTelemetry tracer setup with safe no-op fallback.

When `OTEL_EXPORTER_OTLP_ENDPOINT` is unset (the default for local dev and
tests), this module installs a TracerProvider with no exporter so calls
through `trace.get_tracer(...)` are valid but produce no remote traffic.
When the endpoint is set, spans are batched to the OTLP/gRPC collector and
FastAPI + SQLAlchemy + logging are auto-instrumented.
"""

from __future__ import annotations

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_provider: TracerProvider | None = None


def configure_telemetry(app: FastAPI) -> None:
    """Install tracer provider and instrument the app. Safe to call once."""
    global _provider
    if _provider is not None:
        return

    resource = Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": settings.OTEL_SERVICE_VERSION,
            "deployment.environment": settings.APP_ENV,
        }
    )
    provider = TracerProvider(resource=resource)

    endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT.strip()
    if endpoint:
        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            insecure=settings.OTEL_EXPORTER_OTLP_INSECURE,
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info("otel.configured", endpoint=endpoint, service=settings.OTEL_SERVICE_NAME)
    else:
        logger.info("otel.disabled", reason="OTEL_EXPORTER_OTLP_ENDPOINT empty")

    trace.set_tracer_provider(provider)
    _provider = provider

    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    SQLAlchemyInstrumentor().instrument(tracer_provider=provider)
    LoggingInstrumentor().instrument(set_logging_format=False)


def shutdown_telemetry() -> None:
    """Flush pending spans on app shutdown. Safe to call when not configured."""
    global _provider
    if _provider is None:
        return
    _provider.shutdown()
    _provider = None
