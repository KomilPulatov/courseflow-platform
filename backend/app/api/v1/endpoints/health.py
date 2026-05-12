from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

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
    return {"status": "ok" if checks["postgres"] == "ok" else "degraded", "checks": checks}
