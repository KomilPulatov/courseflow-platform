# Platform Reliability Additions

This folder explains the reliability work added after updating the project to the latest
`origin/main`.

## What Was Already Present

The latest project already had the first layer of this work:

- `docker-compose.yml` already defined PostgreSQL, Redis, RabbitMQ, backend replicas, a Celery worker,
  Nginx, Prometheus, Grafana, and an OpenTelemetry collector.
- `backend/app/modules/platform/celery_app.py` already created a Celery app using RabbitMQ as broker
  and Redis as result backend.
- `backend/app/modules/websocket/manager.py` already had an in-memory WebSocket manager.
- `backend/app/core/telemetry.py` and `backend/app/core/logging.py` already provided OpenTelemetry
  and structured logging.
- `backend/app/modules/registration/repository.py` already used `SELECT ... FOR UPDATE` when loading
  a section for registration, which is the important database lock for the concurrency proof.

## What Was Implemented Now

1. Redis is now used for section availability caching, section availability pub/sub, and a distributed
   registration rate limit.
2. WebSocket backend instances now listen to Redis pub/sub so any backend replica can notify clients
   connected to any other backend replica.
3. RabbitMQ is now used through Celery to process registration events asynchronously and create
   notification rows.
4. Prometheus metrics are exposed from the backend and wired into Prometheus and Grafana.
5. A PostgreSQL concurrency proof script demonstrates that concurrent registration does not overbook
   a section.

## Files In This Folder

- `01-redis-cache-pubsub-rate-limit.md`
- `02-websocket-live-updates.md`
- `03-rabbitmq-celery-events.md`
- `04-observability-metrics.md`
- `05-concurrency-proof.md`
- `06-demo-checklist.md`
