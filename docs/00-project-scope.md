# 00 — Project Scope

## 1. Project identity

**Name:** CRSP — Course Registration and Scheduling Platform

CRSP is an approved course registration and scheduling platform for university use. It helps administrators prepare semesters, professors choose or confirm rooms, and students register for eligible course sections.

## 2. Product problem

Manual or weakly automated course registration causes several problems:

- students register without clear visibility of eligibility;
- professors and administrators struggle to coordinate room allocation;
- course sections can become overloaded;
- timetable conflicts are discovered late;
- registration decisions are hard to audit;
- high-demand registration periods create concurrency risks.

CRSP addresses these problems by combining course registration, academic eligibility checking, professor room selection, timetable suggestion, and concurrency-safe enrollment.

## 3. Actors

### Administrator / Registrar

- Creates semesters.
- Manages departments, majors, courses, professors, rooms, and time slots.
- Creates course offerings and sections.
- Allocates room pools to professors.
- Defines whether room selection is fixed, professor-choice, or system-recommended.
- Defines registration periods and eligibility rules.
- Reviews audit logs and analytics.
- Approves or adjusts timetable suggestions.

### Professor

- Logs in.
- Views assigned courses/sections.
- Chooses or confirms rooms from admin-allocated room pools.
- Views timetable suggestions.
- Views final schedule and rosters.

### Student

- Logs in through INS or creates a manual academic profile.
- Browses eligible courses and sections.
- Views reasons why a course is available/unavailable.
- Registers, drops, swaps, or joins waitlist.
- Views personal timetable.
- Receives live updates and notifications.

### System Worker

- Processes INS sync jobs.
- Processes registration events.
- Generates analytics.
- Runs timetable-suggestion jobs.
- Sends notifications.
- Handles waitlist promotion.

## 4. Student profile scope

CRSP supports two student profile modes.

### INS-verified profile

The student authenticates through IUT INS. The platform stores a local snapshot of trusted academic data.

Possible synced data:

- unique student ID;
- name;
- department;
- major;
- academic year;
- group;
- completed courses;
- current courses;
- GPA;
- academic status.

### Manual profile

The student can skip INS connection and enter required academic data manually through selection cards.

Required manual data:

- unique student ID;
- name;
- department;
- major;
- academic year;
- completed courses selected from official course cards.

Important rule:

**GPA is not considered for manual-profile students.**

Reason: GPA is sensitive and not trusted if entered manually. Prerequisites based on completed-course selections can still be checked.

## 5. In scope for MVP

- Admin setup for semesters, courses, rooms, professors, registration periods.
- Professor room choice from admin-allocated rooms.
- Student INS login path.
- Student manual profile path.
- Course and section browsing.
- Eligibility preview.
- Registration with concurrency safety.
- Drop course.
- Waitlist.
- Basic timetable suggestion.
- WebSocket live seat updates.
- Redis cache/idempotency/rate limiting.
- RabbitMQ/Celery pipeline.
- Token-bucket rate limiter from scratch.
- Docker Compose + Nginx load balancing.
- Observability dashboards.

## 6. Out of scope for MVP

- Perfect automatic university-wide timetable optimization.
- Payment/billing.
- Complex approval workflow from every department.
- Full production-grade INS integration if access is unstable.
- Mobile app.
- AI-generated personalized academic advising.
- Cross-university course exchange.

## 7. MVP positioning

CRSP should be described as:

> A realistic university course registration and scheduling platform that supports real student academic data through optional INS verification, manual-profile fallback, professor room selection, timetable suggestions, and safe concurrent course registration.

## 8. Open decisions

| Decision | Recommended default |
|---|---|
| Student profile mode | Support both INS-verified and manual-profile. |
| GPA for manual students | Skip GPA rules. |
| Room policy | Admin allocates room pool; professor chooses if allowed. |
| Timetable suggestion | Heuristic scoring, not complex AI optimization. |
| Waitlist | Automatic waitlist entry when section is full. |
| Final enrollment truth | PostgreSQL. |
| Cache truth | Redis is not authoritative. |
