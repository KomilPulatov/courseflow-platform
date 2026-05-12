# CRSP — Course Registration and Scheduling Platform

University course registration platform built as a **dockerized modular monolith** for the Database Application and Design course (Spring 2026).

Students search and register for course sections with live seat updates, timetable conflict checks, waitlists, and audit logging. Administrators manage offerings, registration periods, and demand analytics. The central technical challenge is **safe concurrent registration** — the system must never overbook seats under load.

Built by **team Celion**. See `docs/technical-specification.md` for the full spec.

---

## Stack

- **Backend:** FastAPI, SQLAlchemy 2, Alembic, Pydantic v2
- **Database:** PostgreSQL (source of truth) + Redis (cache, idempotency keys, pub/sub)
- **Async:** RabbitMQ + Celery worker
- **Realtime:** WebSockets (live seat updates)
- **Gateway:** Nginx (reverse proxy + load balance across two backend replicas)
- **Observability:** OpenTelemetry, Prometheus, Grafana, Loki/Tempo
- **Frontend:** Static demo console served by FastAPI at `/demo`
- **Package manager:** [`uv`](https://docs.astral.sh/uv/) (single source of truth: `backend/pyproject.toml` + `backend/uv.lock`)

---

## Prerequisites

- Python **3.11+**
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) — install with `curl -LsSf https://astral.sh/uv/install.sh | sh` (or `winget install --id=astral-sh.uv` on Windows)
- Docker Desktop (for the full Postgres / Redis / RabbitMQ / Nginx stack)
- Git

---

## First-time setup

```bash
git clone https://github.com/KomilPulatov/courseflow-platform.git
cd courseflow-platform

# 1. Copy env template
cp .env.example .env

# 2. Backend
cd backend
uv sync
uv run alembic upgrade head
uv run python -m app.db.demo_seed     # demo admin + catalog data
uv run uvicorn app.main:app --reload  # http://localhost:8000/docs

# 3. (Optional but recommended) install pre-commit hooks
cd ..
uv tool install pre-commit
pre-commit install
```

Open:

- http://localhost:8000/docs for the OpenAPI UI
- http://localhost:8000/demo for the seeded demo console
- http://localhost:8000/health for the health check

---

## Common commands

All run from `backend/` unless noted.

| Goal | Command |
|---|---|
| Add a runtime dep | `uv add <pkg>` |
| Add a dev-only dep | `uv add --dev <pkg>` |
| Sync env to lockfile | `uv sync` |
| Apply migrations | `uv run alembic upgrade head` |
| Seed demo data | `uv run python -m app.db.demo_seed` |
| Run server (reload) | `uv run uvicorn app.main:app --reload` |
| Run tests | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Format check (CI-style) | `uv run ruff format --check .` |
| Run all hooks locally | `pre-commit run --all-files` *(from repo root)* |

From the repo root, the full local stack can be validated with:

```bash
docker compose config
docker compose up -d
```

**Never run `pip install` directly** — it bypasses `uv.lock` and breaks reproducibility for the rest of the team. Always go through `uv add` / `uv sync`.

---

## Project structure

```
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
├─ frontend/              # Static demo console mounted at /demo
├─ nginx/                 # reverse proxy + LB config
├─ postgres/              # init.sql, tuning
├─ docs/                  # architecture, ER diagram, BPMN, ADRs
├─ .github/workflows/     # CI
├─ .env.example
├─ CONTRIBUTING.md
└─ CHANGELOG.md
```

---

## Contributing

We use **trunk-based development** with **Conventional Commits**. Before opening a PR, make sure CI passes locally:

```bash
cd backend
uv run ruff check . && uv run ruff format --check . && uv run pytest
```

Full guidelines: [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

[MIT](LICENSE) © 2026 Celion
