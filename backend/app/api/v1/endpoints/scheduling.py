from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.modules.auth.dependencies import require_admin
from app.modules.courses.schemas import ErrorResponse
from app.modules.scheduling.schemas import SuggestionRunCreate, SuggestionRunRead
from app.modules.scheduling.service import SchedulingService

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[User, Depends(require_admin)]


@router.post(
    "/scheduling/suggestion-runs",
    response_model=SuggestionRunRead,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}},
)
def create_suggestion_run(
    payload: SuggestionRunCreate,
    admin: AdminUser,
    db: DbSession,
) -> SuggestionRunRead:
    return SchedulingService(db).create_suggestion_run(
        semester_id=payload.semester_id,
        strategy=payload.strategy,
        admin_user_id=admin.id,
    )


@router.get(
    "/scheduling/suggestion-runs/{run_id}",
    response_model=SuggestionRunRead,
    responses={404: {"model": ErrorResponse}},
)
def get_suggestion_run(
    run_id: int,
    _admin: AdminUser,
    db: DbSession,
) -> SuggestionRunRead:
    return SchedulingService(db).get_run(run_id)


@router.post(
    "/scheduling/suggestion-runs/{run_id}/approve",
    response_model=SuggestionRunRead,
    responses={404: {"model": ErrorResponse}},
)
def approve_suggestion_run(
    run_id: int,
    admin: AdminUser,
    db: DbSession,
) -> SuggestionRunRead:
    return SchedulingService(db).approve_run(run_id, admin.id)
