# Concurrency Proof

## File Locations

- `backend/app/modules/registration/repository.py`
- `backend/app/modules/registration/service.py`
- `backend/scripts/prove_concurrency.py`
- `backend/Dockerfile`

## Important Existing Code

The latest project already had the most important concurrency line:

```python
stmt = select(models.Section).where(models.Section.id == section_id).with_for_update()
```

This is in `RegistrationRepository.get_section_for_update(...)`.

`SELECT ... FOR UPDATE` tells PostgreSQL to lock the selected section row until the transaction commits
or rolls back. When many students try to register for the same section at the same time, only one request
can safely check and update that section at a time.

## Registration Service Flow

`RegistrationService.register(...)` loads the section with `lock_section=True`.

The flow is:

1. Load student, section, offering, course, and semester.
2. Lock the section row.
3. Run eligibility checks.
4. Count current active enrollments.
5. If seats are available, create an enrollment.
6. Otherwise, create a waitlist entry.
7. Commit the transaction.
8. Publish Redis and RabbitMQ side effects after commit.

The lock protects the capacity check and enrollment creation from race conditions.

## Proof Script

`backend/scripts/prove_concurrency.py` creates a demo section with capacity `1` and ten demo students.
It then uses a thread pool to submit ten registrations at nearly the same time:

```python
with ThreadPoolExecutor(max_workers=len(STUDENT_IDS)) as executor:
    futures = [
        executor.submit(register_student, student_id)
        for student_id in STUDENT_IDS
    ]
```

Expected result:

- exactly one student is enrolled
- the remaining students are waitlisted
- the database has exactly one active enrollment row for that section

## How To Run

Use PostgreSQL, not SQLite. SQLite ignores row-level locks, so it is not a valid proof for this feature.

From the project root:

```bash
docker compose up -d postgres redis rabbitmq
docker compose run --rm backend-1 uv run python scripts/prove_concurrency.py
```

Successful output includes:

```text
Expected: exactly 1 enrolled row because section capacity is 1.
Database enrolled rows: 1
```

## Why Side Effects Are After Commit

Redis and RabbitMQ are called after `self.db.commit()`. That means WebSocket messages and Celery tasks
only happen after the database change is real. This keeps the proof focused on database correctness first,
then distributed notifications second.
