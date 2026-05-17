from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.metrics import record_rabbitmq_event
from app.db import models
from app.modules.platform.celery_app import process_registration_event
from app.modules.registration.availability import (
    cache_section_availability,
    calculate_section_availability,
    publish_section_availability,
)

logger = get_logger(__name__)


class AvailabilityPublisher(Protocol):
    def publish_section_changed(self, section_id: int) -> None: ...


class RegistrationEventPublisher(Protocol):
    def publish_registration_event(self, event_type: str, payload: dict) -> None: ...


class NoopAvailabilityPublisher:
    def publish_section_changed(self, section_id: int) -> None:
        return None


class NoopRegistrationEventPublisher:
    def publish_registration_event(self, event_type: str, payload: dict) -> None:
        return None


class RedisAvailabilityPublisher:
    """Updates Redis cache and tells WebSocket listeners that a section changed."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def publish_section_changed(self, section_id: int) -> None:
        if not settings.REDIS_ENABLED:
            return
        availability = calculate_section_availability(self.db, section_id)
        cache_section_availability(availability)
        publish_section_availability(availability)


class CeleryRegistrationEventPublisher:
    """Sends registration events to RabbitMQ through Celery."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def publish_registration_event(self, event_type: str, payload: dict) -> None:
        if not settings.RABBITMQ_ENABLED:
            return

        try:
            process_registration_event.delay(event_type, payload)
            self._mark_event_published(payload.get("registration_event_id"))
            record_rabbitmq_event(event_type, "published")
        except Exception as exc:  # pragma: no cover - depends on external broker
            logger.warning("rabbitmq.publish_failed", event_type=event_type, error=str(exc))
            record_rabbitmq_event(event_type, "error")

    def _mark_event_published(self, registration_event_id: int | None) -> None:
        if registration_event_id is None:
            return
        event = self.db.get(models.RegistrationEvent, registration_event_id)
        if event is None:
            return
        event.published_at = datetime.now(UTC)
        self.db.commit()
