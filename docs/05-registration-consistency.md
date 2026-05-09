# 05 — Registration Consistency

## 1. Main correctness property

CRSP must guarantee:

> A section must never exceed its capacity, even when many students register at the same time.

This is the most important reliability requirement.

## 2. Registration algorithm

Implementation status: Komil's slice implements this flow in the FastAPI backend under
`/api/v1/registrations`. Redis, WebSocket, RabbitMQ, and rate limiting remain adapter
boundaries for the platform reliability slice; registration commits are not dependent
on those services.

```python
def register_student(student_id, section_id, idempotency_key):
    # 1. Check idempotency before doing expensive work.
    # MVP implementation uses PostgreSQL-backed idempotency records.
    cached = idempotency_store.get(student_id, idempotency_key)
    if cached:
        return cached.response

    # 2. Rate limit.
    # Platform slice will plug the Redis token bucket into this boundary.
    rate_limiter.consume_or_raise(student_id, "registration")

    with db.transaction() as tx:
        # 3. Lock selected section.
        section = section_repo.lock_by_id(section_id)  # SELECT ... FOR UPDATE

        # 4. Load student profile.
        student = student_repo.get_with_academic_profile(student_id)

        # 5. Validate registration period.
        rules.ensure_registration_period_open(section.semester_id)

        # 6. Validate profile completeness.
        rules.ensure_student_profile_complete(student)

        # 7. Validate duplicate registration.
        rules.ensure_not_already_registered(
            student_id=student_id,
            course_id=section.course_id,
            semester_id=section.semester_id
        )

        # 8. Validate eligibility.
        rules.ensure_not_already_completed_or_repeat_allowed(student, section.course)
        rules.ensure_department_major_year_allowed(student, section.course)
        rules.ensure_completed_course_prerequisites(student, section.course)

        # 9. GPA behavior depends on profile source.
        if section.course.requires_min_gpa:
            if student.profile_source == "ins_verified":
                rules.ensure_verified_gpa(student, section.course.min_gpa)
            else:
                audit.log("gpa_rule_skipped_manual_profile")

        # 10. Validate timetable and credit limit.
        rules.ensure_no_timetable_conflict(student_id, section_id)
        rules.ensure_credit_limit_not_exceeded(student_id, section.course.credits)

        # 11. Capacity check under lock.
        enrolled_count = enrollment_repo.count_active_by_section(section_id)

        if enrolled_count >= section.capacity:
            waitlist_entry = waitlist_service.join_waitlist_inside_tx(student_id, section_id)
            audit.log_waitlisted(student_id, section_id)
            response = WaitlistedResponse(waitlist_entry)
        else:
            enrollment = enrollment_repo.create(student_id, section_id)
            audit.log_registration_success(student_id, section_id)
            response = EnrolledResponse(enrollment)

        # 12. Save idempotency result.
        idempotency_store.save_after_commit(student_id, idempotency_key, response)

    # 13. Non-critical effects after commit.
    availability_publisher.publish_section_changed(section_id)
    event_publisher.publish_registration_event(response)

    return response
```

## 3. Database protections

The first backend migration adds the registration slice foundation and the defensive
constraints below. Tests create the same schema from SQLAlchemy metadata.

### 3.1 Row lock

```sql
SELECT *
FROM sections
WHERE id = :section_id
FOR UPDATE;
```

This serializes capacity decisions for the same section.

### 3.2 Unique constraints

```sql
UNIQUE(student_id, section_id)
UNIQUE(student_id, course_id, semester_id)
```

These prevent duplicates even if application logic has a bug.

### 3.3 Check constraints

Examples:

```sql
capacity > 0
credits > 0
academic_year BETWEEN 1 AND 6
```

## 4. Student eligibility matrix

| Rule | INS-verified student | Manual-profile student |
|---|---|---|
| Student ID uniqueness | Enforced | Enforced |
| Profile completeness | Enforced | Enforced |
| Department/major/year | Enforced from INS snapshot | Enforced from manual selections |
| Completed prerequisites | Enforced from INS snapshot | Enforced from selected completed courses |
| GPA requirement | Enforced if verified GPA exists | Skipped |
| Already completed | Enforced | Enforced from selected completed courses |
| Already registered | Enforced | Enforced |
| Timetable conflict | Enforced | Enforced |
| Credit limit | Enforced | Enforced |
| Capacity | Enforced under DB lock | Enforced under DB lock |

## 5. Manual profile special rule

Manual-profile students are not blocked by GPA rules. Instead, eligibility output should say:

```json
{
  "rule": "gpa",
  "status": "skipped",
  "message": "GPA is skipped because the student profile is manual and not INS-verified."
}
```

This is more honest and defendable than trusting manually entered GPA.

## 6. Waitlist consistency

When a section is full:

1. Keep the section row locked.
2. Check duplicate waitlist entry.
3. Assign next FIFO position.
4. Insert waitlist entry.
5. Commit.
6. Broadcast waitlist update.

Position query:

```sql
SELECT COALESCE(MAX(position), 0) + 1
FROM waitlist_entries
WHERE section_id = :section_id
FOR UPDATE;
```

Alternative: lock section row and calculate position safely inside the same transaction.

## 7. Drop and promotion consistency

Current slice implementation supports safe student drop by locking the enrollment row
and marking it `dropped`. Automatic waitlist promotion remains a worker/platform
integration task so it does not conflict with the reliability slice.

When a student drops:

1. Begin transaction.
2. Lock enrollment row.
3. Mark enrollment as dropped.
4. Write audit log and registration event.
5. Commit.
6. Publish section-change and registration-event adapter calls.

## 8. Concurrency test

Critical demo test:

> Create one section with capacity 1. Send 50 concurrent registration requests. Expected result: exactly 1 active enrollment; all others are waitlisted or rejected.

Possible command:

```bash
k6 run tests/load/concurrent_registration.js
```

Expected database check:

```sql
SELECT COUNT(*)
FROM enrollments
WHERE section_id = 101 AND status = 'enrolled';
-- must return 1
```

The automated test suite currently covers the capacity invariant, idempotency,
waitlisting, duplicate prevention, drop behavior, and eligibility rule decisions.
A true multi-connection PostgreSQL load test should be run once Docker Compose and
PostgreSQL are wired into the integration environment.

## 9. Failure handling

| Failure | Expected behavior |
|---|---|
| Redis down | Registration still works; idempotency/rate-limit degrade based on configured policy. |
| RabbitMQ down | Registration still commits; event can be retried/outbox if implemented. |
| WebSocket down | Registration still commits; client can refresh. |
| INS down | INS login fails; manual profile path remains available. |
| Backend replica dies | Nginx routes to another replica. |
