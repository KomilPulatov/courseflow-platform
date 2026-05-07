# 07 — Pipeline and BPMN

## 1. Pipeline technology

CRSP uses:

- RabbitMQ as message broker;
- Celery as background worker;
- PostgreSQL for durable results;
- Redis for temporary status/cache.

## 2. Event types

```text
StudentProfileSynced
ManualProfileCreated
ProfessorRoomSelected
TimetableSuggestionRequested
TimetableSuggestionCompleted
StudentRegistered
StudentWaitlisted
StudentDropped
WaitlistPromoted
RegistrationFailed
SectionAvailabilityChanged
```

## 3. Workflow A — INS profile sync

Purpose:

Sync trusted academic data after INS login or manual refresh.

BPMN-style flow:

```mermaid
flowchart TD
    Start((Start)) --> Login[Student requests INS login/sync]
    Login --> Verify[Verify INS credentials]
    Verify --> Valid{Valid?}
    Valid -- No --> Fail[Record sync failure]
    Fail --> End1((End))
    Valid -- Yes --> Fetch[Fetch profile, GPA, completed courses]
    Fetch --> Upsert[Upsert local academic snapshot]
    Upsert --> Event[Publish StudentProfileSynced]
    Event --> Notify[Create notification]
    Notify --> End2((End))
```

Implementation notes:

- Do not store raw INS password.
- Store `last_synced_at`.
- Mark profile source as `ins_verified`.
- If INS is unavailable, user can use manual profile path.

## 4. Workflow B — Manual profile creation

Purpose:

Allow student to skip INS and still use realistic registration flow.

```mermaid
flowchart TD
    Start((Start)) --> Enter[Student enters unique ID and academic selections]
    Enter --> Validate[Validate department, major, year, course selections]
    Validate --> Unique{Student ID unique?}
    Unique -- No --> Reject[Reject duplicate ID]
    Unique -- Yes --> Save[Save manual profile]
    Save --> Mark[Set profile_source = manual]
    Mark --> Audit[Audit ManualProfileCreated]
    Audit --> End((End))
```

Important rule:

- GPA is not considered for manual-profile students.

## 5. Workflow C — Professor room selection

Purpose:

Let professors choose rooms from admin-approved options.

```mermaid
flowchart TD
    Start((Start)) --> View[Professor views assigned sections]
    View --> Options[System loads admin-allocated room options]
    Options --> Choose[Professor selects room]
    Choose --> Validate[Validate room pool, capacity, type, conflict]
    Validate --> OK{Valid?}
    OK -- No --> Reject[Show reason]
    OK -- Yes --> Save[Save room preference/selection]
    Save --> Event[Publish ProfessorRoomSelected]
    Event --> Audit[Audit selection]
    Audit --> End((End))
```

## 6. Workflow D — Timetable suggestion

Purpose:

Generate best-fit timetable options.

```mermaid
flowchart TD
    Start((Start)) --> Request[Admin starts suggestion run]
    Request --> Queue[Publish TimetableSuggestionRequested]
    Queue --> Load[Worker loads courses, rooms, professors, preferences]
    Load --> Generate[Generate candidate schedules]
    Generate --> Score[Score by conflicts, capacity, preferences, demand]
    Score --> Store[Store suggestion run/items]
    Store --> Event[Publish TimetableSuggestionCompleted]
    Event --> Notify[Notify admin/professor]
    Notify --> End((End))
```

MVP algorithm:

```text
score =
  room_capacity_fit
  + professor_preference_match
  + required_course_group_fit
  - room_conflict_penalty
  - professor_conflict_penalty
  - student_group_conflict_penalty
```

## 7. Workflow E — Registration event pipeline

Purpose:

Move non-critical registration work out of the request path.

```mermaid
flowchart TD
    Start((Start)) --> Register[Student registration transaction commits]
    Register --> Publish[Publish StudentRegistered or StudentWaitlisted]
    Publish --> Notify[Worker creates notification]
    Publish --> Analytics[Worker updates demand analytics]
    Publish --> AuditEnrich[Worker enriches event log]
    Notify --> End((End))
    Analytics --> End
    AuditEnrich --> End
```

Critical rule:

> The actual enrollment must be committed before background tasks run.

## 8. Workflow F — Waitlist promotion

Purpose:

Promote or notify next student after a drop.

```mermaid
flowchart TD
    Start((Start)) --> Drop[Student drops course]
    Drop --> Event[Publish StudentDropped]
    Event --> Lock[Worker locks section and first waiting entries]
    Lock --> Find[Find first eligible waitlisted student]
    Find --> Eligible{Eligible?}
    Eligible -- No --> Skip[Mark skipped or keep waiting with reason]
    Skip --> Find
    Eligible -- Yes --> Promote[Create enrollment and mark promoted]
    Promote --> Notify[Notify promoted student]
    Notify --> Broadcast[Broadcast seat/waitlist update]
    Broadcast --> End((End))
```

Recommended MVP:

- Automatic promotion.
- Re-check eligibility before promotion.
- If first student is no longer eligible, continue to next student.

## 9. Outbox option

For stronger reliability, CRSP can implement transactional outbox:

1. Registration transaction writes enrollment.
2. Same transaction writes event row to `registration_events`.
3. Worker reads unsent events and publishes to RabbitMQ.
4. Event status becomes `published`.

MVP can publish directly after commit, but outbox is better for the report if time permits.

## 10. Required screenshots

- RabbitMQ queue with messages.
- Worker logs processing an event.
- Notification created after registration.
- Timetable suggestion run completed.
- Waitlist promotion result.
