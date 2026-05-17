# CourseFlow Platform

CourseFlow is a university course registration and scheduling platform built for
the Database Application and Design course, Spring 2026.

The project is a dockerized platform with a FastAPI backend, PostgreSQL,
Redis, RabbitMQ/Celery, Nginx, observability services, and a React frontend.
Students can browse courses, check section availability, register safely under
concurrent load, join waitlists, and receive live seat updates. Administrators
and professors manage catalog, rooms, schedules, and registration periods.

Built by team Celion.

## Stack

- **Backend:** FastAPI, SQLAlchemy 2, Alembic, Pydantic v2
- **Database:** PostgreSQL (source of truth) + Redis (cache, idempotency keys, pub/sub)
- **Async:** RabbitMQ + Celery worker
- **Realtime:** WebSockets (live seat updates)
- **Gateway:** Nginx (reverse proxy + load balance across two backend replicas)
- **Observability:** OpenTelemetry, Prometheus, Grafana, Loki/Tempo
- **Frontend:** React + TypeScript + Vite single-page app serving both `/demo` and `/admin`
- **Package manager:** [`uv`](https://docs.astral.sh/uv/) (single source of truth: `backend/pyproject.toml` + `backend/uv.lock`)

---

## Prerequisites

- Python 3.11+
- uv
- Node.js 24+
- Docker Desktop
- Git

## Local Development

Copy the environment template first:

```bash
cp .env.example .env
```

Backend:

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run python -m app.db.demo_seed     # demo admin + catalog data
uv run uvicorn app.main:app --reload  # http://localhost:8000/docs

# 3. Frontend
cd ../frontend
npm install
npm run build                         # creates frontend/dist for FastAPI to serve

# 4. (Optional but recommended) install pre-commit hooks
cd ..
uv tool install pre-commit
pre-commit install
```

Frontend:

- http://localhost:8000/docs for the OpenAPI UI
- http://localhost:8000/demo for the seeded demo console
- http://localhost:8000/admin for the admin console
- http://localhost:8000/health for the health check

Open:

- Frontend: http://localhost:5173
- Professor routes: http://localhost:5173/professor
- App utility routes: http://localhost:5173/app
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

The Vite dev server proxies `/api`, `/ws`, `/health`, and `/metrics` to the
local backend.

## Docker Stack

Frontend commands run from `frontend/`:

| Goal | Command |
|---|---|
| Install deps | `npm install` |
| Run dev server | `npm run dev` |
| Run tests | `npm test` |
| Build production assets | `npm run build` |

From the repo root, the full local stack can be validated with:

```bash
docker compose config
docker compose up -d --build
```

Open:

- App through Nginx: http://localhost:8081
- API docs through Nginx: http://localhost:8081/docs
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- RabbitMQ management: http://localhost:15672

Host ports are configured in `.env`, for example `NGINX_PORT=8081`,
`POSTGRES_PORT=5432`, and `GRAFANA_PORT=3000`.

## Common Commands

Backend commands run from `backend/`.

| Goal | Command |
| --- | --- |
| Sync backend deps | `uv sync` |
| Apply migrations | `uv run alembic upgrade head` |
| Seed demo data | `uv run python -m app.db.demo_seed` |
| Run backend | `uv run uvicorn app.main:app --reload` |
| Run backend tests | `uv run pytest` |
| Backend lint | `uv run ruff check .` |
| Backend format check | `uv run ruff format --check .` |

Frontend commands run from `frontend/`.

| Goal | Command |
| --- | --- |
| Install frontend deps | `npm ci` |
| Run frontend dev server | `npm run dev` |
| Build frontend | `npm run build` |
| Lint frontend | `npm run lint` |
| Preview production build | `npm run preview` |

## Project Structure

```text
courseflow-platform/
├─ backend/               # FastAPI app
│  ├─ pyproject.toml      # uv-managed deps + ruff/pytest config
│  ├─ uv.lock             # locked dependency graph (commit this)
│  └─ app/
│     ├─ main.py
│     ├─ api/v1/          # HTTP routers
│     ├─ core/            # config, security, logging, telemetry, rate limiter
│     ├─ db/              # session, transaction helpers
│     ├─ modules/         # auth / courses / registration / waitlist / timetable / audit
│     └─ tests/           # unit / integration / load
├─ frontend/              # React + TypeScript + Vite app mounted at /demo and /admin
├─ nginx/                 # reverse proxy + LB config
├─ postgres/              # init.sql, tuning
├─ docs/                  # architecture, ER diagram, BPMN, ADRs
├─ .github/workflows/     # CI
├─ .env.example
├─ CONTRIBUTING.md
└─ CHANGELOG.md
```

## Pull Request Standard

Before merging a PR, the branch should pass:

```bash
cd backend
uv run ruff check . && uv run ruff format --check . && uv run pytest

cd ../frontend
npm test && npm run build
```

cd ../frontend
npm ci && npm run lint && npm run build

cd ..
docker compose config
```

Use squash merge for feature branches unless the team intentionally wants to
preserve a multi-commit history.

## License

[MIT](LICENSE) (c) 2026 Celion
