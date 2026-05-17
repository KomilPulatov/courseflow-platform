from celery import Celery

from app.core.config import settings
from app.core.logging import get_logger
from app.db import models
from app.db.session import SessionLocal

celery_app = Celery(
    "crsp_worker",
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL,
)
celery_app.conf.task_default_queue = "crsp-events"
celery_app.conf.worker_hijack_root_logger = False
logger = get_logger(__name__)


@celery_app.task(name="platform.process_registration_event")
def process_registration_event(event_type: str, payload: dict) -> dict:
    """Store a simple notification from an async registration event."""

    db = SessionLocal()
    try:
        notification = models.Notification(
            student_id=payload.get("student_id"),
            event_type=event_type,
            message=_message_for(event_type, payload),
            payload=payload,
            status="unread",
        )
        db.add(notification)
        db.commit()
        logger.info("registration_event.processed", event_type=event_type, payload=payload)
        return {"processed": True, "event_type": event_type, "payload": payload}
    finally:
        db.close()


def _message_for(event_type: str, payload: dict) -> str:
    if event_type == "StudentRegistered":
        return f"Registration confirmed for section {payload.get('section_id')}."
    if event_type == "StudentWaitlisted":
        return f"You were added to the waitlist for section {payload.get('section_id')}."
    if event_type == "StudentDropped":
        return f"Registration dropped for section {payload.get('section_id')}."
    return "Registration event was processed."
