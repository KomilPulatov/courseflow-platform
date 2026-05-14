from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.modules.platform.celery_app import celery_app
from app.modules.platform.redis_client import get_redis_client

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.get("")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/dependencies")
def dependency_health(db: DbSession) -> dict[str, Any]:
    checks: dict[str, Any] = {
        "postgres": "unknown",
        "redis": "not_configured",
        "rabbitmq": "not_configured",
        "ins": "mock_or_http",
    }
    try:
        db.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as exc:  # pragma: no cover - defensive health surface
        checks["postgres"] = f"error: {exc}"

    if settings.REDIS_ENABLED:
        try:
            client = get_redis_client()
            checks["redis"] = "ok" if client is not None and client.ping() else "error"
        except Exception as exc:  # pragma: no cover - external dependency
            checks["redis"] = f"error: {exc}"

    if settings.RABBITMQ_ENABLED:
        try:
            with celery_app.connection_for_write() as connection:
                connection.ensure_connection(max_retries=1)
            checks["rabbitmq"] = "ok"
        except Exception as exc:  # pragma: no cover - external dependency
            checks["rabbitmq"] = f"error: {exc}"

    required = ["postgres"]
    if settings.REDIS_ENABLED:
        required.append("redis")
    if settings.RABBITMQ_ENABLED:
        required.append("rabbitmq")
    status_value = "ok" if all(checks[item] == "ok" for item in required) else "degraded"
    return {"status": status_value, "checks": checks}
