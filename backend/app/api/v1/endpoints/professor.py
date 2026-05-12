from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.modules.auth.dependencies import require_professor
from app.modules.rooms.schemas import (
    ProfessorSectionRead,
    RoomOptionsResponse,
    RoomPreferenceCreate,
    RoomPreferenceRead,
)
from app.modules.rooms.service import RoomService

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
ProfessorUser = Annotated[User, Depends(require_professor)]


@router.get("/sections", response_model=list[ProfessorSectionRead])
def list_sections(current_user: ProfessorUser, db: DbSession) -> list[ProfessorSectionRead]:
    return RoomService(db).list_professor_sections(current_user.id)


@router.get("/sections/{section_id}/room-options", response_model=RoomOptionsResponse)
def room_options(
    section_id: int,
    current_user: ProfessorUser,
    db: DbSession,
) -> RoomOptionsResponse:
    return RoomService(db).room_options(user_id=current_user.id, section_id=section_id)


@router.post("/sections/{section_id}/room-preferences", response_model=RoomPreferenceRead)
def choose_room(
    section_id: int,
    payload: RoomPreferenceCreate,
    current_user: ProfessorUser,
    db: DbSession,
) -> RoomPreferenceRead:
    return RoomService(db).choose_room(
        user_id=current_user.id,
        section_id=section_id,
        payload=payload,
    )
