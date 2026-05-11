# 10 — Team Plan

## 1. Team

- Komil
- Azamat
- Bekzod
- Iftikhor
- Farrukh

## 2. Main principle

Do **not** split the project like this:

```text
one person frontend
one person backend
one person database
one person testing
one person deployment
```

That creates weak understanding, merge conflicts, and poor viva readiness.

Instead, CRSP should be built with **vertical feature slices**.

Each member owns one feature slice end-to-end:

```text
database migration
+ backend model/service/API
+ small UI integration
+ tests
+ docs/report paragraph
+ screenshots
```

Everyone touches backend, database, frontend, tests, and docs, but in different feature areas.

## 3. Vertical slice ownership

| Member | Primary slice | End-to-end responsibility |
|---|---|---|
| Komil | Academic profile and eligibility | Academic profile foundation, eligibility orchestration, real-life eligibility rules, integration with registration checks. |
| Azamat | Auth, identity, and onboarding | INS/manual onboarding, student identity uniqueness, auth flows, INS adapter, sync logs, profile entry UX. |
| Bekzod | Catalog and demo surface | Course catalog, offerings, prerequisites, academic setup screens, demo UI flows, and API docs. |
| Iftikhor | Rooms and scheduling | Room allocation/selection, professor room flow, room validation, timetable suggestion algorithm/UI/tests. |
| Farrukh | Registration and platform reliability | Registration flow, waitlist, consistency guarantees, Redis/WebSocket/RabbitMQ pipeline, observability, load/concurrency proof. |

This is not “backend vs frontend.” It is feature ownership. For example, Azamat’s slice includes DB tables, API endpoints, frontend forms, tests, and docs for student profiles.

## 4. Buddy review system

Every slice needs one reviewer.

| Owner | Reviewer |
|---|---|
| Komil | Farrukh |
| Azamat | Komil |
| Bekzod | Azamat |
| Iftikhor | Bekzod |
| Farrukh | Iftikhor |

Reviewer checks:

- migration quality;
- API naming;
- business rule correctness;
- frontend flow;
- tests;
- documentation;
- whether owner can explain it.

## 5. Shared ownership rules

### Database

- Each slice owner creates migrations only for their own feature.
- One person cannot rewrite another person’s tables without discussion.
- Use small migrations.
- Avoid giant `init_all_tables.py` after the first schema version.
- Before merging, run migrations from scratch.

### Backend

- Each slice owns module folder:
  - `student_profiles`
  - `admin`
  - `registration`
  - `rooms`
  - `scheduling`
  - `platform`

- Shared interfaces go through PR review.

### Frontend

- Each slice owner creates the screens needed for their feature.
- Use shared components, but avoid editing the same page at the same time.
- Route ownership should be clear:
  - `/student/profile`
  - `/admin/courses`
  - `/professor/rooms`
  - `/student/register`
  - `/admin/observability-demo`

### Tests

Every slice must include:

- at least one unit test;
- at least one integration/API test;
- at least one screenshot-ready demo scenario.

### Docs

Every slice owner updates the related doc file:

| Slice | Docs to update |
|---|---|
| Registration | `05-registration-consistency.md`, `04-api-contract.md` |
| Student profiles | `01-requirements.md`, `03-data-model.md`, `04-api-contract.md` |
| Admin setup | `01-requirements.md`, `03-data-model.md` |
| Professor rooms/scheduling | `02-architecture.md`, `03-data-model.md`, `07-pipeline-and-bpmn.md` |
| Platform reliability | `06-polyglot-persistence.md`, `08-observability.md`, `09-deployment.md` |

## 6. Branch strategy

Recommended branch naming:

```text
feature/student-profile-manual-ins
feature/admin-academic-setup
feature/professor-room-selection
feature/registration-consistency
feature/platform-redis-ws-pipeline
fix/...
docs/...
```

Merge rule:

- no direct push to `main`;
- each PR needs one reviewer;
- PR must include screenshots or test output when possible;
- do not merge broken Docker Compose.

## 7. Integration order

### Phase 1 — Foundation

All members help.

- Repo setup.
- Docker Compose skeleton.
- FastAPI app.
- PostgreSQL + Alembic.
- Basic frontend shell.
- Auth skeleton.
- Shared coding conventions.

### Phase 2 — Core vertical slices

| Slice | Owner |
|---|---|
| Student INS/manual profile | Azamat |
| Admin academic setup | Bekzod |
| Professor room selection | Iftikhor |
| Registration rules and consistency | Komil |
| Redis/WebSocket/RabbitMQ/rate limiter | Farrukh |

### Phase 3 — Integration

All members join.

- Connect student profile to eligibility.
- Connect admin course rules to registration.
- Connect professor room choices to timetable.
- Connect WebSocket to registration.
- Connect worker pipeline to events.
- Run full demo flow.

### Phase 4 — Hardening

All members join.

- Concurrency test.
- Seed data.
- Error handling.
- Observability screenshots.
- Deployment.
- Report.

## 8. Final demo scenario

The team should build one strong demo path:

```text
Admin creates semester, course, professor, rooms, prerequisites
→ Admin allocates room options
→ Professor chooses room
→ Admin runs timetable suggestion
→ Student creates manual profile or logs in via INS
→ Student sees eligibility result
→ Student registers
→ WebSocket seat count updates
→ RabbitMQ worker creates notification
→ Audit log shows trace
→ Grafana/SigNoz shows metric/trace/log
```

## 9. Definition of done for every feature

A feature is not done until it has:

- migration;
- seed data if needed;
- API endpoint;
- service/repository logic;
- frontend screen or minimal UI;
- test;
- OpenAPI example;
- audit/log event if important;
- doc update;
- screenshot/demo evidence.

## 10. Contribution fairness

The official project may check GitHub history. To show balanced contribution:

- every member commits code, not only docs;
- every member owns one vertical slice;
- every member reviews another slice;
- every member contributes to final integration;
- every member can explain registration flow, database design, Redis/RabbitMQ role, and deployment.
