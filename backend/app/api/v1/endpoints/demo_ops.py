from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_student_id
from app.api.pagination import Page
from app.db import models
from app.db.session import get_db
from app.modules.audit.schemas import AuditLogRead
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


@router.get("/admin/audit-logs", response_model=Page[AuditLogRead])
def list_audit_logs(
    _admin: Annotated[models.User, Depends(require_admin)],
    db: DbSession,
    event_type: str | None = None,
    entity_type: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[AuditLogRead]:
    stmt = select(models.AuditLog)
    count_stmt = select(func.count()).select_from(models.AuditLog)
    if event_type:
        stmt = stmt.where(models.AuditLog.event_type == event_type)
        count_stmt = count_stmt.where(models.AuditLog.event_type == event_type)
    if entity_type:
        stmt = stmt.where(models.AuditLog.entity_type == entity_type)
        count_stmt = count_stmt.where(models.AuditLog.entity_type == entity_type)
    if created_from is not None:
        stmt = stmt.where(models.AuditLog.created_at >= created_from)
        count_stmt = count_stmt.where(models.AuditLog.created_at >= created_from)
    if created_to is not None:
        stmt = stmt.where(models.AuditLog.created_at <= created_to)
        count_stmt = count_stmt.where(models.AuditLog.created_at <= created_to)
    rows = db.execute(
        stmt.order_by(models.AuditLog.created_at.desc()).offset(offset).limit(limit)
    ).scalars()
    return Page(
        items=[
            AuditLogRead(
                id=row.id,
                actor_student_id=row.actor_student_id,
                event_type=row.event_type,
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                payload=row.payload,
                created_at=row.created_at,
            )
            for row in rows
        ],
        total=int(db.execute(count_stmt).scalar_one()),
        limit=limit,
        offset=offset,
    )
