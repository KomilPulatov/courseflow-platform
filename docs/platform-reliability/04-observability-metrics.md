# Observability And Metrics

## File Locations

- `backend/app/core/metrics.py`
- `backend/app/main.py`
- `backend/app/core/logging.py`
- `backend/app/core/telemetry.py`
- `observability/prometheus.yml`
- `observability/grafana/dashboards.yml`
- `observability/grafana/dashboards/crsp-platform.json`
- `observability/grafana/datasources/datasources.yml`
- `docker-compose.yml`

## Existing Observability

The latest project already had:

- structured logging with `structlog`
- OpenTelemetry setup for FastAPI, SQLAlchemy, and logging
- an OpenTelemetry collector config
- Prometheus and Grafana containers

## What Was Added

`backend/app/core/metrics.py` adds Prometheus metrics that are easy to explain:

```python
HTTP_REQUESTS
HTTP_REQUEST_SECONDS
REGISTRATION_EVENTS
REDIS_OPERATIONS
RABBITMQ_EVENTS
WEBSOCKET_CONNECTIONS
```

These names tell students exactly what is being measured.

## HTTP Middleware

`MetricsMiddleware` measures each HTTP request:

```python
start = perf_counter()
response = await call_next(request)
elapsed = perf_counter() - start
```

Then it increments a counter and records request duration. This gives visibility into API traffic and
latency.

## Metrics Endpoint

`backend/app/main.py` exposes:

```python
@app.get("/metrics", include_in_schema=False)
def prometheus_metrics():
    return metrics_response()
```

Prometheus scrapes this endpoint from both backend replicas.

## Prometheus Configuration

`observability/prometheus.yml` now has:

```yaml
- job_name: crsp-backend
  metrics_path: /metrics
  static_configs:
    - targets: [backend-1:8000, backend-2:8000]
```

This proves both replicas are observable.

## Grafana Dashboard

`observability/grafana/dashboards/crsp-platform.json` includes panels for:

- registration events
- Redis operations
- RabbitMQ events
- open WebSocket connections

The dashboard is provisioned automatically through `observability/grafana/dashboards.yml`.

## How To Explain This

OpenTelemetry is used for traces and logs. Prometheus is used for numeric metrics. Grafana reads from
Prometheus and displays the dashboard. Together, these let students observe what the distributed platform
is doing during registration, caching, WebSocket updates, and background jobs.
