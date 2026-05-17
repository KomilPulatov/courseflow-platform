from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.modules.auth.dependencies import require_admin
from app.modules.scheduling.schemas import (
    SuggestionApproveResponse,
    SuggestionRunCreate,
    SuggestionRunRead,
    SuggestionRunStartResponse,
    SuggestionRunSummary,
)
from app.modules.scheduling.service import SchedulingService

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[User, Depends(require_admin)]


@router.post(
    "/suggestion-runs",
    response_model=SuggestionRunStartResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_suggestion_run(
    payload: SuggestionRunCreate,
    current_user: AdminUser,
    db: DbSession,
) -> SuggestionRunStartResponse:
    return SchedulingService(db).create_run(payload, requested_by_user_id=current_user.id)


@router.get("/suggestion-runs", response_model=list[SuggestionRunSummary])
def list_suggestion_runs(
    _admin: AdminUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[SuggestionRunSummary]:
    return SchedulingService(db).list_runs(limit=limit)


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
