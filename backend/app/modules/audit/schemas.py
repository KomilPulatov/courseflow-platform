from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: int
    actor_student_id: int | None
    event_type: str
    entity_type: str
    entity_id: int | None
    payload: dict[str, Any] | None
    created_at: datetime
