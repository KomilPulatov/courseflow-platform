from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.modules.auth.dependencies import require_admin
from app.modules.courses.schemas import ErrorResponse
from app.modules.rooms.schemas import (
    ProfessorCreate,
    ProfessorRead,
    ProfessorUpdate,
    RoomAllocationCreate,
    RoomAllocationRead,
    RoomCreate,
    RoomRead,
    RoomUpdate,
)
from app.modules.rooms.service import RoomService

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[User, Depends(require_admin)]


# ── Rooms ─────────────────────────────────────────────────────────────────────


@router.get("/rooms", response_model=list[RoomRead])
def list_rooms(_admin: AdminUser, db: DbSession) -> list[RoomRead]:
    return RoomService(db).list_rooms()


@router.post(
    "/rooms",
    response_model=RoomRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
def create_room(
    payload: RoomCreate,
    _admin: AdminUser,
    db: DbSession,
) -> RoomRead:
    return RoomService(db).create_room(payload)


@router.patch(
    "/rooms/{room_id}",
    response_model=RoomRead,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def update_room(
    room_id: int,
    payload: RoomUpdate,
    _admin: AdminUser,
    db: DbSession,
) -> RoomRead:
    return RoomService(db).update_room(room_id, payload)


# ── Room allocations ──────────────────────────────────────────────────────────


@router.get(
    "/sections/{section_id}/room-allocations",
    response_model=list[RoomAllocationRead],
)
def list_room_allocations(
    section_id: int,
    _admin: AdminUser,
    db: DbSession,
) -> list[RoomAllocationRead]:
    return RoomService(db).list_allocations(section_id)


@router.post(
    "/sections/{section_id}/room-allocations",
    response_model=list[RoomAllocationRead],
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}},
)
def allocate_rooms(
    section_id: int,
    payload: RoomAllocationCreate,
    admin: AdminUser,
    db: DbSession,
) -> list[RoomAllocationRead]:
    return RoomService(db).allocate_rooms(
        section_id=section_id,
        payload=payload,
        allocated_by_user_id=admin.id,
    )


@router.delete(
    "/sections/{section_id}/room-allocations/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def remove_room_allocation(
    section_id: int,
    room_id: int,
    _admin: AdminUser,
    db: DbSession,
) -> None:
    RoomService(db).remove_allocation(section_id, room_id)


# ── Professors (admin CRUD) ───────────────────────────────────────────────────


@router.get("/professors", response_model=list[ProfessorRead])
def list_professors(_admin: AdminUser, db: DbSession) -> list[ProfessorRead]:
    return RoomService(db).list_professors()


@router.post(
    "/professors",
    response_model=ProfessorRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
def create_professor(
    payload: ProfessorCreate,
    _admin: AdminUser,
    db: DbSession,
) -> ProfessorRead:
    return RoomService(db).create_professor(payload)


@router.patch(
    "/professors/{professor_id}",
    response_model=ProfessorRead,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def update_professor(
    professor_id: int,
    payload: ProfessorUpdate,
    _admin: AdminUser,
    db: DbSession,
) -> ProfessorRead:
    return RoomService(db).update_professor(professor_id, payload)
