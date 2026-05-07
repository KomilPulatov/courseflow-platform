# 01 — Requirements

## 1. Requirement compliance summary

CRSP must satisfy the official DAD project requirements:

| ID | Requirement | CRSP implementation |
|---|---|---|
| R1 | Business scenario and requirements | Course registration and scheduling platform with admin, professor, student, INS/manual profile, timetable and registration flows. |
| R2 | Diagrams | ERD, relational schema, system architecture, project structure, Docker dependency graph, BPMN workflows. |
| R3 | Relational DBMS | PostgreSQL + Alembic migrations + seed data. |
| R4 | RESTful API | FastAPI + OpenAPI/Swagger. |
| R5 | Polyglot persistence | Redis key-value store. |
| R6 | Cache/index/storage optimization | Redis cache + Postgres indexes + measured latency improvements. |
| R7 | Additional API style | WebSocket live updates. |
| R8 | API gateway/load balancing | Nginx + two FastAPI replicas. |
| R9 | Docker Compose | Full stack started by `docker compose up -d`. |
| R10 | Batch/stream pipeline | RabbitMQ + Celery workflows documented with BPMN. |
| R11 | From-scratch component | Token-bucket rate limiter. |
| R12 | Observability | Traces, logs, metrics in one stack. |
| R13 | Documentation | README, docs, OpenAPI, CHANGELOG, deployment guide. |

## 2. Functional requirements

### FR1 — Authentication and profiles

The system shall support:

- admin login;
- professor login;
- student login through INS;
- manual student profile creation;
- JWT-based API access;
- role-based permissions.

Acceptance criteria:

- A student ID must be unique.
- A user has exactly one main role for MVP: `admin`, `professor`, or `student`.
- A student profile has a source: `ins_verified` or `manual`.

### FR2 — INS student verification

The system shall allow a student to verify through IUT INS.

Primary flow:

1. Student selects “Continue with INS”.
2. Student enters INS credentials or uses configured INS connector.
3. Backend verifies the credentials.
4. Backend creates/updates local user.
5. Backend syncs student academic profile.
6. Student is marked as `ins_verified`.

Data to sync when available:

- student ID;
- full name;
- department;
- major;
- academic year;
- completed courses;
- GPA;
- academic status.

Fallback:

- If INS is unavailable, the student can use manual profile mode.

### FR3 — Manual student profile

The system shall allow a student to skip INS verification and manually enter academic information.

Primary flow:

1. Student selects “Create manual profile”.
2. Student enters unique student ID.
3. Student chooses department, major, academic year.
4. Student selects completed courses from cards.
5. Backend stores profile as `manual`.
6. GPA rules are skipped for this student.

Acceptance criteria:

- Student ID uniqueness is enforced.
- Manual completed courses must reference existing official courses.
- Manual GPA is not accepted for eligibility decisions.

### FR4 — Admin academic setup

The system shall allow admins to manage:

- semesters;
- departments;
- majors;
- courses;
- course prerequisites;
- eligibility rules;
- professors;
- rooms;
- time slots;
- course offerings;
- sections;
- registration periods.

Acceptance criteria:

- Admin can create a course offering for a semester.
- Admin can assign professor to offering/section.
- Admin can allocate rooms to professor/section.
- Admin can open/close registration.

### FR5 — Professor room selection

The system shall allow professors to choose or confirm rooms from admin-allocated options.

Room-selection modes:

- `admin_fixed`: room already fixed by admin;
- `professor_choice`: professor chooses one room from allowed pool;
- `system_recommended`: system recommends best room/time option.

Validation:

- selected room must be in allocated pool;
- room capacity must fit section capacity;
- room type must match course needs;
- room must not conflict with another section at same time.

### FR6 — Timetable suggestions

The system shall suggest best-fit timetable options using available constraints.

Inputs:

- rooms;
- time slots;
- professors;
- professor choices;
- section capacity;
- expected demand;
- required courses by department/major/year;
- conflict rules.

Outputs:

- suggested room/time combinations;
- conflict warnings;
- score/reasoning for suggested option.

### FR7 — Course browsing and eligibility preview

Students shall be able to browse courses and sections.

Each section should show:

- course code/title;
- credits;
- professor;
- room;
- time;
- capacity;
- remaining seats;
- waitlist count;
- eligibility status.

Eligibility statuses:

- `eligible`;
- `missing_prerequisite`;
- `department_restricted`;
- `major_restricted`;
- `year_restricted`;
- `gpa_rule_skipped_manual_profile`;
- `gpa_too_low`;
- `timetable_conflict`;
- `already_completed`;
- `already_registered`;
- `section_full_waitlist_available`.

### FR8 — Registration

A student can register for a section only if:

- registration period is open;
- student profile is complete;
- student is not already registered for same course in same semester;
- student has not already completed the course unless repeat is allowed;
- prerequisites are satisfied;
- department/major/year rules pass;
- GPA rule passes if student is INS-verified and course requires GPA;
- GPA rule is skipped if student is manual-profile;
- credit limit is not exceeded;
- timetable does not conflict;
- section has capacity.

### FR9 — Drop course

A student can drop a course before the drop deadline.

After drop:

- enrollment status becomes `dropped`;
- seat becomes available;
- waitlist workflow is triggered;
- live seat update is broadcast.

### FR10 — Waitlist

If a section is full:

- student can join waitlist;
- position is FIFO;
- duplicate waitlist entries are blocked;
- when a seat opens, first eligible student can be promoted or notified.

Recommended MVP policy:

- automatic promotion after drop if the next waitlisted student is still eligible.

### FR11 — Live updates

The system shall use WebSocket to push:

- section availability updates;
- waitlist position changes;
- registration results;
- scheduling update notifications.

### FR12 — Audit logs

The system shall log:

- login attempts;
- INS sync result;
- manual profile creation/update;
- professor room selection;
- admin course/room/period changes;
- registration success/failure;
- waitlist join/promotion;
- rate-limit rejection.

## 3. Non-functional requirements

### Reliability

- No overbooking under concurrent registration.
- Database constraints protect correctness.
- Registration transaction is atomic.
- Redis failure must not corrupt final registration state.
- Audit logs should help debug every important action.

### Scalability

Assumed scale for demo/report:

| Item | Target |
|---|---:|
| Students | 1,000–5,000 |
| Courses | 100–300 |
| Sections | 300–800 |
| Peak registration attempts | 100 concurrent users |
| Catalog p95 latency | < 200 ms cached |
| Registration p95 latency | < 500 ms under moderate load |

### Maintainability

- Modular monolith.
- Clear service/repository boundaries.
- Business rules not placed directly in route handlers.
- Every feature has tests and docs.
- Team members work in vertical slices.

### Security

- Passwords are never stored in plain text.
- INS credentials are not stored unless absolutely necessary; prefer short-lived verification.
- Manual profiles are marked as unverified.
- Admin/professor endpoints require role authorization.
- Audit logs avoid storing sensitive raw credentials.

## 4. Open questions

1. Will professor accounts be local demo accounts or connected to university login?
2. Should manual-profile students be allowed to edit completed courses after registering?
3. Should GPA rules be fully skipped for manual students or shown as “requires INS verification”?
4. Should waitlist promotion be automatic or offer-based?
5. Should timetable suggestion happen before professor room choice, after it, or both?
