# Registration and Waitlist Implementation Guide

This guide explains the backend work added for registration, waitlist, and consistency.
It is written for team members who need to understand and explain the feature during
the project submission.

## What Was Created

The feature lets a student register for a course section safely. If the section still
has seats, the student becomes enrolled. If the section is full, the student is placed
on a FIFO waitlist. When an enrolled student drops the section, the backend automatically
promotes the first still-eligible waitlisted student.

The important consistency rule is:

> A section must never have more active enrollments than its capacity.

The backend protects this by locking the section row during seat decisions and by using
database uniqueness constraints for duplicate registrations and waitlist entries.

## Main User Flows

### Register for a section

Endpoint:

```text
POST /api/v1/registrations
```

Request:

```json
{
  "section_id": 1,
  "idempotency_key": "student-click-1"
}
```

The service:

1. Checks idempotency so repeated clicks return the same result.
2. Locks the section row with `SELECT ... FOR UPDATE`.
3. Loads student, course, semester, and section data.
4. Runs eligibility checks.
5. Counts current active enrollments.
6. Creates either an `enrolled` enrollment or a `waiting` waitlist entry.
7. Writes audit/event rows and commits.

### Join waitlist directly

Endpoint:

```text
POST /api/v1/waitlists
```

This endpoint is only for full sections. If seats are still available, the API returns
`section_has_available_seats` so the student registers normally instead.

### Drop and auto-promote

Endpoint:

```text
DELETE /api/v1/registrations/{enrollment_id}
```

The service:

1. Locks the enrollment.
2. Locks the section.
3. Marks the enrollment as `dropped`.
4. Looks at waitlist entries in FIFO order.
5. Re-checks eligibility for each waiting student.
6. Promotes the first eligible student.
7. Marks ineligible waiting students as `skipped`.

Example drop response with promotion:

```json
{
  "status": "dropped",
  "enrollment_id": 1,
  "section_id": 1,
  "promoted": {
    "student_id": 2,
    "enrollment_id": 2,
    "waitlist_entry_id": 1
  }
}
```

## Files Modified

### `backend/app/api/deps.py`

Adds the current-student resolver used by registration and waitlist endpoints.
It supports two identity modes:

- `Authorization: Bearer <token>` for real student login.
- `X-Student-Id` for Swagger demos and tests.

JWT is preferred when both are present.

### `backend/app/api/v1/endpoints/waitlists.py`

New API router for waitlist actions:

- `GET /api/v1/waitlists/me`
- `POST /api/v1/waitlists`
- `DELETE /api/v1/waitlists/{entry_id}`

The route functions stay thin. They validate the request shape, load the current
student ID, and call `RegistrationService`.

### `backend/app/api/v1/router.py`

Registers the new waitlist router under:

```text
/api/v1/waitlists
```

### `backend/app/api/v1/endpoints/registrations.py`

Updates the drop endpoint response model so the API documents whether a waitlisted
student was promoted.

### `backend/app/modules/registration/schemas.py`

Adds Pydantic models for:

- direct waitlist join request;
- waitlist list item;
- waitlist cancellation response;
- drop response;
- promoted student details.

These models define the JSON shapes visible in Swagger/OpenAPI.

### `backend/app/modules/registration/errors.py`

Adds business errors for waitlist behavior:

- `section_has_available_seats`
- `waitlist_entry_not_active`

### `backend/app/modules/registration/repository.py`

Adds database helper methods for:

- locking waitlist rows;
- reading FIFO waitlist entries;
- listing a student's waiting entries;
- reusing inactive waitlist rows when a student rejoins.

The rejoin behavior matters because the database allows only one waitlist row per
student and section.

### `backend/app/modules/registration/service.py`

Contains the main business logic:

- idempotent registration;
- enroll-or-waitlist decision;
- direct waitlist join;
- waitlist cancellation;
- waitlist listing;
- drop with FIFO auto-promotion;
- skipped waitlist entries for students who became ineligible.

This is the best file to study when explaining how the feature works.

### `backend/app/tests/test_registration_api.py`

Adds and updates tests for:

- enrollment when capacity is available;
- waitlisting when full;
- no overbooking;
- drop with no promotion;
- drop with FIFO promotion;
- skipping ineligible waitlisted students;
- waitlist join/list/cancel/rejoin;
- JWT student identity.

### `backend/scripts/seed_registration_demo.py`

Creates repeatable demo data:

- one semester;
- one course;
- one section with capacity 1;
- open registration period;
- three complete manual students.

Run it from `backend/`:

```bash
uv run python scripts/seed_registration_demo.py
```

Then use the printed student IDs in Swagger with `X-Student-Id`.

### Documentation Files

The following docs were updated so the written specification matches the code:

- `README.md`
- `CHANGELOG.md`
- `docs/04-api-contract.md`
- `docs/05-registration-consistency.md`

## How To Explain Consistency

The key idea is that registration is not decided from cached data or frontend state.
The backend starts a transaction and locks the section row before counting enrollments.
That means two requests for the same section cannot safely make the seat decision at
the exact same time in PostgreSQL.

If the count is below capacity, the service creates an enrollment. If the count is at
capacity, the service creates a waitlist entry instead. The database also has uniqueness
constraints to prevent duplicate enrollment or duplicate waitlist rows.

## Demo Script Flow

After running the seed script:

1. Start the backend.
2. Open Swagger at `/docs`.
3. Use student 1 to call `POST /api/v1/registrations`.
4. Use student 2 to call `POST /api/v1/registrations`.
5. Student 2 should be waitlisted because the section capacity is 1.
6. Use student 2 to call `GET /api/v1/waitlists/me`.
7. Use student 1 to call `DELETE /api/v1/registrations/{enrollment_id}`.
8. Student 2 should be promoted automatically.

## Notes For The Team

- Redis, RabbitMQ, WebSockets, and frontend UI are not part of this slice.
- SQLite tests check the logic, but the real row-locking guarantee is a PostgreSQL feature.
- The code intentionally keeps service methods explicit so junior developers can trace
  the flow without understanding a complex abstraction.
