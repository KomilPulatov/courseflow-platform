# RabbitMQ And Celery Events

## File Locations

- `backend/app/modules/platform/celery_app.py`
- `backend/app/modules/registration/publishers.py`
- `backend/app/modules/registration/service.py`
- `backend/app/modules/registration/repository.py`
- `docker-compose.yml`

## What Was Already Present

The latest project already created a Celery app:

```python
celery_app = Celery(
    "crsp_worker",
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL,
)
```

RabbitMQ is the broker. Redis is the Celery result backend.

## What Was Added

`CeleryRegistrationEventPublisher` was added in `backend/app/modules/registration/publishers.py`.

The registration service now publishes successful registration events after the database transaction
commits:

```python
self.event_publisher.publish_registration_event(
    event_type,
    self._event_payload(registration_event, response_body),
)
```

Publishing after commit matters because the worker should not process an event for a database change that
was rolled back.

## Event Row Tracking

`RegistrationRepository.add_registration_event(...)` now returns the created `RegistrationEvent` row:

```python
event = models.RegistrationEvent(...)
self.db.add(event)
self.db.flush()
return event
```

The publisher uses that id to mark `published_at` after Celery accepts the task.

## Worker Task

`backend/app/modules/platform/celery_app.py` contains:

```python
@celery_app.task(name="platform.process_registration_event")
def process_registration_event(event_type: str, payload: dict) -> dict:
```

The task creates a simple `Notification` row for the student. This is intentionally small and readable:
it proves that RabbitMQ/Celery is doing real background work without adding complicated business logic.

## Why This Is A Good University-Level Design

The registration request stays fast and focused:

1. Validate rules.
2. Write enrollment or waitlist row.
3. Commit the database transaction.
4. Publish a background event.

The slower side effect, notification creation, is handled by a worker. Students can explain the separation
between synchronous critical data changes and asynchronous follow-up processing.

## Failure Behavior

If RabbitMQ is unavailable, the publisher catches the exception, logs it, and records a metric. The
student registration itself stays committed because the main database transaction already succeeded.
