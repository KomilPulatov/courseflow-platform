from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_student_id
from app.db import models
from app.db.session import get_db
from app.modules.auth.dependencies import require_admin

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/notifications/me")
def list_my_notifications(
    student_id: Annotated[int, Depends(get_current_student_id)],
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
) -> list[dict[str, Any]]:
    rows = db.execute(
        select(models.Notification)
        .where(models.Notification.student_id == student_id)
        .order_by(models.Notification.created_at.desc())
        .limit(limit)
    ).scalars()
    return [
        {
            "id": row.id,
            "event_type": row.event_type,
            "message": row.message,
            "payload": row.payload,
            "status": row.status,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.get("/admin/audit-logs")
def list_audit_logs(
    _admin: Annotated[models.User, Depends(require_admin)],
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[dict[str, Any]]:
    rows = db.execute(
        select(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(limit)
    ).scalars()
    return [
        {
            "id": row.id,
            "actor_student_id": row.actor_student_id,
            "event_type": row.event_type,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "payload": row.payload,
            "created_at": row.created_at,
        }
        for row in rows
    ]
