from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.modules.auth.dependencies import require_admin
from app.modules.scheduling.schemas import (
    SuggestionApproveResponse,
    SuggestionRunCreate,
    SuggestionRunRead,
    SuggestionRunStartResponse,
)
from app.modules.scheduling.service import SchedulingService

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[User, Depends(require_admin)]


@router.post(
    "/suggestion-runs",
    response_model=SuggestionRunRead,
    status_code=status.HTTP_201_CREATED,
)
def create_suggestion_run(
    payload: SuggestionRunCreate,
    current_user: AdminUser,
    db: DbSession,
) -> SuggestionRunRead:
    return SchedulingService(db).create_run(payload, requested_by_user_id=current_user.id)


@router.get("/suggestion-runs/{run_id}", response_model=SuggestionRunRead)
def get_suggestion_run(run_id: int, _admin: AdminUser, db: DbSession) -> SuggestionRunRead:
    return SchedulingService(db).get_run(run_id)


@router.post("/suggestion-runs/{run_id}/approve", response_model=SuggestionApproveResponse)
def approve_suggestion_run(
    run_id: int,
    _admin: AdminUser,
    db: DbSession,
) -> SuggestionApproveResponse:
    return SchedulingService(db).approve_run(run_id)
