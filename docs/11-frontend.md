# 11 - Frontend

## Purpose

The frontend is the single CourseFlow React app. It lives in `frontend/`, calls
the FastAPI API, stores demo auth tokens in browser local storage, and listens
to WebSocket updates for registration and waitlist events.

The same Vite build owns all browser routes:

```text
/                     redirects to the unified login route
/login                unified student, professor, and admin login
/demo                 demo console for the complete academic workflow
/admin/*              admin catalog, delivery, scheduling, and ops console
/professor/*          professor dashboard, sections, room options, timetable
/app/*                operational health/settings utility pages
```

## Local Development

```bash
cd frontend
npm ci
npm run dev
```

The dev server runs on http://localhost:5173 and proxies these paths to the
backend on http://localhost:8000:

```text
/api
/ws
/health
/metrics
```

Set `VITE_API_BASE` only when the frontend is served from a different origin.
For same-origin Nginx deployment, keep it empty.

## Production Build

```bash
cd frontend
npm run lint
npm run build
```

The Docker image builds the Vite static files and serves them through an
internal Nginx container. The root Compose Nginx forwards public `/` traffic to
that frontend container. Backend-only routes such as `/api`, `/ws`, `/docs`,
`/health`, and `/metrics` are proxied to FastAPI by the root Nginx service.

## Integration Contract

- API paths must stay under `/api/v1`.
- WebSocket paths must stay under `/ws`.
- Browser routes belong in `frontend/src/router.tsx`, not in FastAPI.
- Feature UI belongs inside the single `frontend/src/` app. Do not add nested
  Vite apps or commit generated `dist/`/prebuilt browser assets.
- Browser-facing environment variables must be prefixed with `VITE_`.
- `package-lock.json` is committed and CI uses `npm ci`.
- Generated folders such as `node_modules/` and `dist/` are ignored.
