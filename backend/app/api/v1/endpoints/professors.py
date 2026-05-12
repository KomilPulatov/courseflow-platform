from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.modules.auth.dependencies import require_professor
from app.modules.courses.schemas import ErrorResponse
from app.modules.professors.errors import (
    RoomCapacityError,
    RoomConflictError,
    RoomNotInPoolError,
    SectionNotAssignedError,
)
from app.modules.professors.schemas import (
    AssignedSectionRead,
    RoomPreferenceCreate,
    RoomPreferenceRead,
)
from app.modules.professors.service import ProfessorService

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
ProfessorUser = Annotated[User, Depends(require_professor)]


@router.get("/sections", response_model=list[AssignedSectionRead])
def list_assigned_sections(
    professor: ProfessorUser,
    db: DbSession,
) -> list[AssignedSectionRead]:
    return ProfessorService(db).list_assigned_sections(professor.id)


@router.get(
    "/sections/{section_id}/room-options",
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def get_room_options(
    section_id: int,
    professor: ProfessorUser,
    db: DbSession,
) -> dict:
    try:
        return ProfessorService(db).get_room_options(professor.id, section_id)
    except SectionNotAssignedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)


@router.post(
    "/sections/{section_id}/room-preferences",
    response_model=RoomPreferenceRead,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def save_room_preference(
    section_id: int,
    payload: RoomPreferenceCreate,
    professor: ProfessorUser,
    db: DbSession,
) -> RoomPreferenceRead:
    try:
        return ProfessorService(db).save_room_preference(professor.id, section_id, payload)
    except SectionNotAssignedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except RoomNotInPoolError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RoomCapacityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RoomConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
