from time import perf_counter

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings

HTTP_REQUESTS = Counter(
    "crsp_http_requests_total",
    "HTTP requests received by the FastAPI backend.",
    ["method", "path", "status"],
)
HTTP_REQUEST_SECONDS = Histogram(
    "crsp_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "path"],
)
REGISTRATION_EVENTS = Counter(
    "crsp_registration_events_total",
    "Registration decisions recorded by the registration service.",
    ["event_type", "result"],
)
REDIS_OPERATIONS = Counter(
    "crsp_redis_operations_total",
    "Redis cache, pub/sub, and rate-limit operations.",
    ["operation", "result"],
)
RABBITMQ_EVENTS = Counter(
    "crsp_rabbitmq_events_total",
    "Registration events submitted to Celery/RabbitMQ.",
    ["event_type", "result"],
)
WEBSOCKET_CONNECTIONS = Gauge(
    "crsp_websocket_connections",
    "Current WebSocket connections grouped by channel type.",
    ["channel"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Small Prometheus middleware kept explicit for student readability."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not settings.METRICS_ENABLED:
            return await call_next(request)

        start = perf_counter()
        response = await call_next(request)
        path = request.scope.get("route").path if request.scope.get("route") else request.url.path
        elapsed = perf_counter() - start

        HTTP_REQUESTS.labels(
            method=request.method,
            path=path,
            status=str(response.status_code),
        ).inc()
        HTTP_REQUEST_SECONDS.labels(method=request.method, path=path).observe(elapsed)
        return response


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def record_registration_event(event_type: str, result: str) -> None:
    if settings.METRICS_ENABLED:
        REGISTRATION_EVENTS.labels(event_type=event_type, result=result).inc()


def record_redis_operation(operation: str, result: str) -> None:
    if settings.METRICS_ENABLED:
        REDIS_OPERATIONS.labels(operation=operation, result=result).inc()


def record_rabbitmq_event(event_type: str, result: str) -> None:
    if settings.METRICS_ENABLED:
        RABBITMQ_EVENTS.labels(event_type=event_type, result=result).inc()


def set_websocket_connections(channel: str, count: int) -> None:
    if settings.METRICS_ENABLED:
        WEBSOCKET_CONNECTIONS.labels(channel=channel).set(count)
