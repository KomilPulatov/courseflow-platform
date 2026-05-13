# 04 — API Contract

Base URL:

```text
/api/v1
```

## 1. Authentication

### POST `/auth/admin/login`

Admin login.

Request:

```json
{
  "email": "admin@crsp.local",
  "password": "secret"
}
```

Response:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "role": "admin"
}
```

### POST `/auth/professor/login`

Professor login.

### POST `/auth/student/ins-login`

Student login through IUT INS.

Request:

```json
{
  "student_number": "2310204",
  "password": "ins-password"
}
```

Response:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "profile_source": "ins_verified",
  "student": {
    "student_number": "2310204",
    "full_name": "Komilkhuja Pulatov",
    "department": "ICE",
    "major": "Information and Computer Engineering",
    "current_gpa": 4.5,
    "gpa_is_verified": true
  }
}
```

### POST `/auth/student/manual-start`

Creates/starts manual student account.

Request:

```json
{
  "student_number": "2310204",
  "full_name": "Komilkhuja Pulatov",
  "email": "student@example.com",
  "password": "secret"
}
```

Response:

```json
{
  "access_token": "...",
  "profile_source": "manual",
  "requires_profile_completion": true
}
```

## 2. Student profile

### GET `/student-profiles/me`

Returns current student profile.

### PUT `/student-profiles/me/manual`

Updates manual academic profile.

Request:

```json
{
  "department_id": 1,
  "major_id": 2,
  "academic_year": 3,
  "group_name": "ICE-21-01",
  "completed_course_codes": ["MSC1010", "CSE2010", "CSE2020"]
}
```

Response:

```json
{
  "profile_source": "manual",
  "student_number": "2310204",
  "profile_complete": true,
  "gpa_rules_enabled": false
}
```

### POST `/student-profiles/me/sync-ins`

Refreshes profile from INS for INS-verified students.

## 3. Admin academic setup

### POST `/admin/semesters`

### POST `/admin/departments`

### POST `/admin/majors`

### POST `/admin/courses`

### PUT `/admin/courses/{course_id}/prerequisites`

Replaces the full prerequisite set for the course in one transaction.

### POST `/admin/courses/{course_id}/eligibility-rules`

### POST `/admin/professors`

### POST `/admin/rooms`

### POST `/admin/course-offerings`

### POST `/admin/sections`

Create section.

Request:

```json
{
  "course_offering_id": 10,
  "professor_id": 5,
  "section_code": "001",
  "capacity": 30,
  "room_selection_mode": "professor_choice"
}
```

### POST `/admin/sections/{section_id}/room-allocations`

Admin allocates room options.

Request:

```json
{
  "room_ids": [1, 2, 3],
  "notes": "Professor may choose one of these rooms."
}
```

### POST `/admin/registration-periods`

Open or configure registration period.

Supporting list endpoints now available for the demo/admin console:

- `GET /admin/majors?department_id=<id>`
- `GET /admin/semesters`
- `GET /admin/courses`
- `GET /admin/course-offerings?semester_id=<id>`
- `GET /admin/sections?course_id=<id>&semester_id=<id>`
- `GET /admin/registration-periods?semester_id=<id>`

## 4. Professor flow

### GET `/professor/sections`

Returns assigned sections.

### GET `/professor/sections/{section_id}/room-options`

Returns admin-allocated room options.

Response:

```json
{
  "section_id": 101,
  "room_selection_mode": "professor_choice",
  "options": [
    {
      "room_id": 1,
      "building": "B",
      "room_number": "305",
      "capacity": 35,
      "room_type": "lecture",
      "available": true
    }
  ]
}
```

### POST `/professor/sections/{section_id}/room-preferences`

Request:

```json
{
  "room_id": 1,
  "preference_rank": 1
}
```

Response:

```json
{
  "status": "selected",
  "message": "Room preference saved."
}
```

## 5. Scheduling

### POST `/admin/scheduling/suggestion-runs`

Starts timetable suggestion.

Request:

```json
{
  "semester_id": 1,
  "strategy": "balanced_heuristic"
}
```

Response:

```json
{
  "run_id": 88,
  "status": "queued"
}
```

### GET `/admin/scheduling/suggestion-runs/{run_id}`

Returns generated options.

### POST `/admin/scheduling/suggestion-runs/{run_id}/approve`

Approves a suggested timetable.

## 6. Courses and sections

### GET `/courses`

Query parameters:

- `semester_id`
- `department_id`
- `major_id`
- `search`
- `eligible_only`

### GET `/courses/{course_id}`

Returns course metadata plus prerequisite course cards.

### GET `/courses/{course_id}/sections`

### GET `/sections/{section_id}`

### GET `/sections/{section_id}/availability`

Current implementation note:
- `eligible_only=true` requires a student JWT bearer token.
- Public catalog responses are backed by real `courses`, `course_offerings`, `sections`, and enrollment counts.

## 7. Eligibility

### GET `/sections/{section_id}/eligibility`

Returns eligibility for current student.

Student identity is provided by a student JWT bearer token.

Response:

```json
{
  "section_id": 101,
  "eligible": true,
  "profile_source": "manual",
  "gpa_rules_enabled": false,
  "checks": [
    {
      "rule": "prerequisite",
      "status": "passed",
      "message": "Required courses are completed."
    },
    {
      "rule": "gpa",
      "status": "skipped",
      "message": "GPA is skipped because the student profile is manual and not INS-verified."
    },
    {
      "rule": "capacity",
      "status": "passed",
      "message": "4 seats remaining."
    }
  ]
}
```

## 8. Registration

### POST `/registrations`

Student identity is provided by a student JWT bearer token.

Request:

```json
{
  "section_id": 101,
  "idempotency_key": "8e03b2cc-7f9e-4371-a2d2-321ea1cabc15"
}
```

Success response:

```json
{
  "status": "enrolled",
  "enrollment_id": 9001,
  "section_id": 101,
  "remaining_seats": 4
}
```

Waitlist response:

```json
{
  "status": "waitlisted",
  "waitlist_entry_id": 55,
  "position": 3
}
```

Failure response:

```json
{
  "error": "missing_prerequisite",
  "message": "You have not completed CSE2020."
}
```

### DELETE `/registrations/{enrollment_id}`

Drops course.

Response:

```json
{
  "status": "dropped",
  "enrollment_id": 9001,
  "section_id": 101
}
```

### GET `/registrations/me`

### GET `/registrations/me/timetable`

## 9. Waitlist

### GET `/waitlists/me`

### POST `/waitlists`

### DELETE `/waitlists/{entry_id}`

## 10. WebSocket API

### `/ws/sections/{section_id}`

Event:

```json
{
  "type": "section.availability.updated",
  "section_id": 101,
  "remaining_seats": 3,
  "waitlist_count": 8,
  "occurred_at": "2026-05-07T10:00:00Z"
}
```

### `/ws/registrations/me`

Event:

```json
{
  "type": "registration.result",
  "status": "enrolled",
  "section_id": 101,
  "message": "Registration successful."
}
```

## 11. Common error codes

| HTTP code | Meaning |
|---:|---|
| 400 | Invalid request or business rule violation |
| 401 | Not authenticated |
| 403 | Role not allowed |
| 404 | Resource not found |
| 409 | Conflict: duplicate, full section, timetable conflict, capacity race |
| 422 | Schema validation error |
| 429 | Rate limit exceeded |
| 503 | Dependency unavailable |
