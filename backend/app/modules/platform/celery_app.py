from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "crsp_worker",
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL,
)
celery_app.conf.task_default_queue = "crsp-events"
celery_app.conf.worker_hijack_root_logger = False


@celery_app.task(name="platform.process_registration_event")
def process_registration_event(event_type: str, payload: dict) -> dict:
    return {"processed": True, "event_type": event_type, "payload": payload}
