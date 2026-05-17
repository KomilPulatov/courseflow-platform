# 11 - Frontend

## Purpose

The frontend is the student-facing CourseFlow React app. It lives in
`frontend/`, calls the FastAPI API, stores the demo student token in browser
local storage, and listens to WebSocket updates for registration and waitlist
events.

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
that frontend container.

## Integration Contract

- API paths must stay under `/api/v1`.
- WebSocket paths must stay under `/ws`.
- Browser-facing environment variables must be prefixed with `VITE_`.
- `package-lock.json` is committed and CI uses `npm ci`.
- Generated folders such as `node_modules/` and `dist/` are ignored.
