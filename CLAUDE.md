# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All backend commands run from `backend/` unless noted.

```bash
uv sync                                                    # install/sync deps from lockfile
uv run alembic upgrade head                                # apply DB migrations
uv run python -m app.db.demo_seed                          # seed demo data
uv run uvicorn app.main:app --reload                       # dev server → http://localhost:8000
uv run pytest                                              # full test suite
uv run pytest app/tests/test_auth_api.py::test_name        # single test
uv run ruff check . && uv run ruff format .                # lint + format
pre-commit run --all-files                                 # all hooks (from repo root)
docker compose up -d                                       # full stack (nginx:8081, grafana:3000, rabbitmq:15672)
```

**Never run `pip install` directly** — always `uv add` / `uv sync`.

To reset the local SQLite DB: delete `backend/crsp.db`, then re-run `alembic upgrade head`.

## Frontend (frontend-student/)

```bash
cd frontend-student
npm install
npm run dev        # dev server → http://localhost:5173
npm run build      # production build
```

API base URL is set in `frontend-student/.env.local` (`VITE_API_BASE`). Local default: `http://localhost:8000`. Live server: `http://138.68.83.15:8081`.

## Architecture

**Modular monolith** — one FastAPI codebase run as two replicas behind Nginx.

```
backend/app/
  api/v1/endpoints/   — thin HTTP handlers, no business logic
  modules/            — feature modules, each owns service + schemas
  api/deps.py         — central dependency wiring (auth, DB session, services)
  core/config.py      — all settings and feature toggles
  db/                 — SQLAlchemy base, session, migrations, seed
```

Feature modules: `auth`, `students`, `registration`, `waitlist`, `courses`, `rooms`, `scheduling`, `platform`.

`api/deps.py` is the seam between HTTP and business logic. Key dependencies:
- `get_current_student_id()` — decodes JWT Bearer token; dev fallback: `X-Student-Id` header
- `get_registration_service()` — wires Redis/Celery publishers into the registration service
- `DbSession` — SQLAlchemy session with auto-close

All feature toggles (`REDIS_ENABLED`, `RABBITMQ_ENABLED`, `WEBSOCKET_REDIS_BRIDGE_ENABLED`, `REGISTRATION_RATE_LIMIT_ENABLED`) default to `false` in local dev. The app runs correctly without Redis, RabbitMQ, or observability services.

## Data layer

- **PostgreSQL** — source of truth for all enrollment state
- **Redis** — non-authoritative: section availability cache (TTL 30 s), idempotency key store, token-bucket rate limiter, WebSocket pub/sub bridge
- **RabbitMQ + Celery** — async event pipeline: notifications, audit, waitlist promotion
- **SQLite** — default for local dev (`backend/crsp.db`); PostgreSQL used in Docker

## Registration safety

The core invariant is that a section never exceeds capacity under concurrent load:

1. Client sends unique `idempotency_key` (UUID) with every registration POST
2. Server checks `RegistrationIdempotencyKey` table — same hash → return cached response immediately
3. `SELECT ... FOR UPDATE` on the section row serialises all capacity decisions for that section
4. Eligibility checks run under the lock
5. Insert `Enrollment` (or `WaitlistEntry` if full), commit, then publish events
6. Unique constraints `(student_id, section_id)` and `(student_id, course_id, semester_id)` are the final safeguard

On drop: the next waitlist entry is promoted to enrolled within the same transaction.

## Student profile modes

- `ins_verified` — scraped from IUT INS portal; GPA is trusted and used in eligibility checks
- `manual` — user-entered; GPA rules are **skipped entirely** (shown as `"skipped"`, never `"failed"`)

After `POST /auth/student/manual-start`, the response includes `requires_profile_completion: true`. The student must call `PUT /student-profiles/me/manual` before registering.

## WebSockets

- `/ws/sections/{section_id}` — live seat/availability updates; no JWT required
- `/ws/registrations/{user_id}` — enrollment result events for a student

These have no `/api/v1` prefix and are mounted directly on the FastAPI app.

## Demo seed accounts

- Admin: `admin@crsp.example.com` / `admin12345`
- Professor: `professor@crsp.example.com` / `prof12345`
- Student: `student@crsp.example.com` / `student12345`

Live server: `http://138.68.83.15:8081` (nginx), Grafana: `:3000`, RabbitMQ UI: `:15672`.
