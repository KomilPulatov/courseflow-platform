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

- Backend: FastAPI, SQLAlchemy 2, Alembic, Pydantic v2
- Frontend: one React, TypeScript, Vite, Tailwind, React Router app in `frontend/`
- Database: PostgreSQL, Redis
- Async: RabbitMQ and Celery
- Realtime: WebSockets
- Gateway: Nginx reverse proxy with two backend replicas
- Observability: OpenTelemetry, Prometheus, Grafana, Loki, Tempo
- Backend package manager: uv
- Frontend package manager: npm

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
uv run python -m app.db.demo_seed
uv run uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm ci
npm run dev
```

Open:

- Frontend: http://localhost:5173
- Professor routes: http://localhost:5173/professor
- App utility routes: http://localhost:5173/app
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

The Vite dev server proxies `/api`, `/ws`, `/health`, and `/metrics` to the
local backend.

## Docker Stack

From the repository root:

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
  backend/               FastAPI app, migrations, tests
  frontend/              React app for student, professor, and app utility routes
  nginx/                 Public reverse proxy config
  postgres/              PostgreSQL init scripts
  observability/         OTel, Prometheus, Grafana, Loki, Tempo config
  docs/                  Requirements, architecture, API, deployment notes
  .github/workflows/     CI for backend, frontend, and Compose config
```

## Pull Request Standard

Before merging a PR, the branch should pass:

```bash
cd backend
uv run ruff check . && uv run ruff format --check . && uv run pytest

cd ../frontend
npm ci && npm run lint && npm run build

cd ..
docker compose config
```

Use squash merge for feature branches unless the team intentionally wants to
preserve a multi-commit history.

## License

[MIT](LICENSE) (c) 2026 Celion
