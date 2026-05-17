# Demo Checklist

## Start The Platform

From the project root:

```bash
docker compose up --build
```

Useful URLs:

- API through Nginx: `http://localhost:8080`
- API docs: `http://localhost:8080/docs`
- RabbitMQ UI: `http://localhost:15672`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

RabbitMQ default login:

- username: `guest`
- password: `guest`

Grafana default login:

- username: `admin`
- password: `admin`

## Health Checks

Backend health:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/health/dependencies
```

Metrics:

```bash
curl http://localhost:8080/metrics
```

Prometheus query examples:

```text
crsp_http_requests_total
crsp_registration_events_total
crsp_redis_operations_total
crsp_rabbitmq_events_total
crsp_websocket_connections
```

## Redis Demo

Call section availability twice. The first call calculates from PostgreSQL. The second call can hit Redis:

```bash
curl http://localhost:8080/api/v1/sections/1/availability
curl http://localhost:8080/api/v1/sections/1/availability
```

Then check Prometheus for:

```text
crsp_redis_operations_total
```

## WebSocket Demo

Open a WebSocket client to:

```text
ws://localhost:8080/ws/sections/1
```

Then perform a registration or waitlist action for section `1`. The WebSocket should receive a
`section_availability_changed` payload.

## RabbitMQ Demo

Register or drop a student. Then check:

1. RabbitMQ queue activity in `http://localhost:15672`.
2. `crsp_rabbitmq_events_total` in Prometheus.
3. `notifications` table in PostgreSQL.

The Celery worker consumes the event and creates a notification row.

## Concurrency Proof

Run:

```bash
docker compose run --rm backend-1 uv run python scripts/prove_concurrency.py
```

The important output is:

```text
Database enrolled rows: 1
Expected: exactly 1 enrolled row because section capacity is 1.
```

That proves concurrent requests do not overbook the section.
