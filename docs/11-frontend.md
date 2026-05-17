# 11 - Frontend

## Purpose

The frontend is a React/Vite operations console for the CourseFlow platform. It
is intentionally thin: it calls the FastAPI API directly, keeps auth tokens in
browser local storage for demo workflows, and surfaces API responses in an event
log so reviewers can verify behavior quickly.

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

Set `VITE_API_BASE_URL` only when the frontend is served from a different origin.
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
