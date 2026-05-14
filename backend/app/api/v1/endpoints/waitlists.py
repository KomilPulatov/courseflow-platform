from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_student_id
from app.db.session import get_db
from app.modules.registration.publishers import RedisAvailabilityPublisher
from app.modules.waitlists.schemas import WaitlistCreate, WaitlistDeleteResponse, WaitlistItem
from app.modules.waitlists.service import WaitlistService

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/me", response_model=list[WaitlistItem])
def list_my_waitlists(
    student_id: Annotated[int, Depends(get_current_student_id)],
    db: DbSession,
) -> list[WaitlistItem]:
    return WaitlistService(db).list_current(student_id)


@router.post("", response_model=WaitlistItem, status_code=status.HTTP_201_CREATED)
def join_waitlist(
    payload: WaitlistCreate,
    student_id: Annotated[int, Depends(get_current_student_id)],
    db: DbSession,
) -> WaitlistItem:
    return WaitlistService(db, RedisAvailabilityPublisher(db)).join(student_id, payload)


@router.delete("/{waitlist_entry_id}", response_model=WaitlistDeleteResponse)
def cancel_waitlist(
    waitlist_entry_id: int,
    student_id: Annotated[int, Depends(get_current_student_id)],
    db: DbSession,
) -> WaitlistDeleteResponse:
    return WaitlistService(db, RedisAvailabilityPublisher(db)).cancel(student_id, waitlist_entry_id)
