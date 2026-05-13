# 09 — Deployment

## 1. Deployment goal

CRSP must run as a multi-service stack on a remote VM with one public entry point through Nginx.

Expected command:

```bash
docker compose up -d
```

## 2. Services

```text
nginx
frontend
backend-1
backend-2
postgres
redis
rabbitmq
worker
otel-collector
prometheus
grafana
loki
tempo
```

Minimum acceptable:

```text
nginx
frontend
backend-1
backend-2
postgres
redis
rabbitmq
worker
prometheus
grafana
otel-collector
```

Current repository implementation serves the static demo frontend from FastAPI at `/demo`;
Nginx proxies `/demo`, `/api/*`, and `/ws/*` to the backend pool.

## 3. Docker dependency graph

```mermaid
flowchart TD
    nginx --> frontend
    nginx --> backend1
    nginx --> backend2

    backend1 --> postgres
    backend2 --> postgres

    backend1 --> redis
    backend2 --> redis

    backend1 --> rabbitmq
    backend2 --> rabbitmq
    worker --> rabbitmq
    worker --> postgres
    worker --> redis

    backend1 --> otel
    backend2 --> otel
    worker --> otel

    otel --> prometheus
    prometheus --> grafana
    otel --> tempo
    otel --> loki
```

## 4. Nginx responsibilities

- Expose single public port.
- Serve frontend.
- Route `/api/*` to backend pool.
- Route `/ws/*` to backend pool.
- Load-balance backend replicas.
- Forward request IDs.
- Terminate TLS in production.

Example:

```nginx
upstream backend_pool {
    server backend-1:8000;
    server backend-2:8000;
}

server {
    listen 80;

    location / {
        proxy_pass http://frontend:3000;
    }

    location /api/ {
        proxy_pass http://backend_pool;
        proxy_set_header Host $host;
        proxy_set_header X-Request-ID $request_id;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /ws/ {
        proxy_pass http://backend_pool;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 5. Environment variables

```env
APP_ENV=production
DATABASE_URL=postgresql+asyncpg://crsp:password@postgres:5432/crsp
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
JWT_SECRET=change-me
ACCESS_TOKEN_EXPIRE_MINUTES=60

INS_MODE=mock
INS_BASE_URL=https://ins.inha.uz
INS_TIMEOUT_SECONDS=10

OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

## 6. INS deployment policy

Use `INS_MODE`:

```text
mock       - use fake connector for local/demo
http       - use real HTTP connector if available
disabled   - allow manual profile only
```

This avoids blocking development if INS is unavailable.

## 7. Health checks

Every service should have health checks.

Backend:

```text
GET /api/v1/health
GET /api/v1/health/dependencies
```

Dependency health:

- PostgreSQL connection;
- Redis ping;
- RabbitMQ connection;
- INS connector mode/status.

## 8. VM deployment checklist

1. Create remote VM.
2. Install Docker and Docker Compose plugin.
3. Clone GitHub repo.
4. Copy `.env.example` to `.env`.
5. Configure domain or public IP.
6. Run `docker compose up -d`.
7. Run migrations.
8. Seed data.
9. Check `/docs`.
10. Check Nginx public route.
11. Check WebSocket route.
12. Capture screenshots for report.

## 9. Repository hygiene

Must exclude:

```text
node_modules/
__pycache__/
.venv/
dist/
build/
.cache/
coverage/
*.log
.env
```

## 10. Release

Before submission:

```bash
git tag v1.0
git push origin v1.0
```

Prepare:

```text
report.pdf
LINKS.txt
```

`LINKS.txt` should contain:

```text
Deployed URL:
GitHub URL:
Team roster:
```
