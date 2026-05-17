# 11 — Admin Frontend Implementation Plan

## 1. Purpose

This document records the second-pass implementation that replaced the original static frontend
with a React application and completed the admin roadmap that had been left open after the first
vanilla-SPA pass.

The project now uses one React + TypeScript + Vite codebase for both:

```text
/demo
/admin
```

The migration goal was not just “rewrite the UI in React.” It was to finish the missing admin
capabilities while leaving the project easier to extend than the earlier single-file JavaScript app.

---

## 2. Final product goal

Create a modular admin experience for:

```text
/admin
/admin/semesters
/admin/departments
/admin/majors
/admin/courses
/admin/courses/new
/admin/courses/:courseId
/admin/courses/:courseId/prerequisites
/admin/courses/:courseId/eligibility-rules
/admin/professors
/admin/rooms
/admin/offerings
/admin/sections
/admin/sections/:sectionId
/admin/sections/:sectionId/rooms
/admin/registration-periods
/admin/scheduling
/admin/scheduling/:runId
/admin/audit-logs
/admin/observability
```

### Success criteria

- Replace the old static frontend architecture with React as the primary framework.
- Keep `/demo` available while moving it into the same typed React application.
- Avoid a monolithic `App.jsx`; organize code by app shell, shared UI, and feature modules.
- Complete Milestones A and B from the earlier plan:
  - edit/update flows
  - archive-oriented lifecycle management
  - room deallocation
  - eligibility-rule update/delete
  - scheduling enrichment
  - server-side filtering and pagination
- Preserve clean browser URLs and direct-refresh support through FastAPI SPA fallback routing.
- Keep Docker deployment simple: `docker compose up --build` must build the frontend automatically.

---

## 3. Architecture decisions

| Area | Decision |
|---|---|
| Frontend framework | React 19 + TypeScript + Vite |
| Routing | React Router |
| Server state | TanStack Query |
| Forms | React Hook Form |
| App shape | One React app serving both `/demo` and `/admin` |
| Backend serving | FastAPI serves `frontend/dist` SPA assets |
| Admin lifecycle model | Archive-first instead of destructive deletes for core academic entities |
| Paginated response shape | `{ items, total, limit, offset }` |
| Core paginated lists | courses, sections, scheduling runs, audit logs |
| Room deallocation rule | Block removal if the professor currently selected that room |

---

## 4. What was implemented

### 4.1 React migration

The previous static files were replaced by a modular React codebase:

```text
frontend/
├─ index.html
├─ package.json
├─ vite.config.ts
├─ tsconfig.json
└─ src/
   ├─ app/
   │  ├─ providers.tsx
   │  └─ router.tsx
   ├─ components/
   │  └─ ui.tsx
   ├─ features/
   │  ├─ admin/
   │  │  ├─ AdminLayout.tsx
   │  │  ├─ LoginPage.tsx
   │  │  ├─ catalog-pages.tsx
   │  │  ├─ delivery-pages.tsx
   │  │  └─ ops-pages.tsx
   │  └─ demo/
   │     └─ DemoPage.tsx
   ├─ lib/
   │  ├─ api.ts
   │  └─ types.ts
   └─ styles/
      ├─ admin.css
      └─ demo.css
```

The old legacy files under `frontend/app.js`, `frontend/styles.css`, and `frontend/admin/`
were removed after the React cutover.

### 4.2 Admin functionality completed

| Area | Completed work |
|---|---|
| Core edit flows | semesters, departments, majors, courses, professors, rooms, offerings, sections, registration periods |
| Archive flows | archive-aware updates for departments, majors, courses, professors, rooms, offerings, semesters |
| Safe archival rules | archive attempts are blocked while active dependents still exist |
| Course maintenance | edit course details, replace prerequisites, create/update/delete eligibility rules |
| Section safety | reject section-capacity reductions below active enrollment count |
| Room management | add and remove room allocations; block deallocation when a selected professor preference exists |
| Scheduling overview | enriched summaries with `semester_name`, filtering, pagination |
| Audit logs | server-side filtering and pagination, including date-range support |
| Admin dashboard | summary counts, health, recent audit activity |
| Demo parity | original demo workflows preserved inside React |

### 4.3 Backend/API work

Backend support added for:

- archive state on departments, majors, courses, and professors
- PATCH endpoints for the core admin entities
- admin course-detail endpoint that can view archived courses
- eligibility-rule PATCH and DELETE endpoints
- room-allocation DELETE endpoint
- paginated admin course, section, scheduling-run, and audit-log lists
- scheduling-run summaries enriched with semester names
- public course/section reads that hide archived academic records

### 4.4 Build and deployment work

- Added a frontend CI job for install, test, and build.
- Converted the backend Dockerfile into a multi-stage build that compiles React assets first.
- Updated Compose to build from the repository root so backend images can include frontend assets.
- Updated FastAPI SPA routing to serve both `/demo` and `/admin` from the built React bundle.

---

## 5. Business rules implemented

The admin frontend is backed by explicit safety rules rather than optimistic UI-only behavior:

- A department cannot be archived while it still has active majors or active courses.
- A semester cannot be archived while it still has active offerings.
- A course cannot be archived while active offerings remain.
- An offering cannot be archived while active sections remain.
- A professor cannot be archived while assigned to active sections.
- A room cannot be archived while allocated to active sections.
- A section capacity cannot be reduced below active enrollment count.
- A room allocation cannot be removed while a professor has selected that room.

---

## 6. Verification completed

Validation after the React migration and admin completion:

```bash
cd frontend
npm test
npm run build

cd ../backend
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest
```

Observed result:

- frontend tests: **2 passed**
- frontend production build: **passed**
- backend Ruff: **passed**
- backend tests: **44 passed**

Additional backend regression coverage now verifies:

- dependency-aware archive blocking
- section capacity protection
- selected-room deallocation blocking
- eligibility-rule update/delete
- React SPA fallback routing
- paginated scheduling-run responses

---

## 7. Remaining work

The original Milestones A and B are complete. The remaining work is now product hardening rather
than missing core admin functionality:

- richer browser-level end-to-end coverage
- accessibility pass
- better entity pickers instead of raw ID inputs
- confirmation dialogs for destructive/archive actions
- more polished optimistic/error states
- stronger production session handling than local-storage demo tokens
- richer dashboard visualizations

---

## 8. Files introduced or changed

### New frontend files

```text
frontend/package.json
frontend/package-lock.json
frontend/vite.config.ts
frontend/tsconfig.json
frontend/src/**
```

### New backend files

```text
backend/app/api/pagination.py
backend/app/db/migrations/versions/0006_admin_completion.py
backend/app/modules/audit/schemas.py
backend/app/tests/test_admin_completion_api.py
```

### Important updated files

```text
backend/app/main.py
backend/Dockerfile
docker-compose.yml
.github/workflows/ci.yml
README.md
docs/04-api-contract.md
docs/09-deployment.md
```

---

## 9. Final status

The requested migration and implementation are complete:

- the frontend now uses React as the main framework
- `/demo` and `/admin` share one typed frontend application
- the admin roadmap from the first implementation pass has been completed
- the codebase is modular instead of concentrated in one oversized app file
- local verification and automated tests pass
