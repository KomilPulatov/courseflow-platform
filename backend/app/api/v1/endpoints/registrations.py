from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_student_id
from app.db.session import get_db
from app.modules.registration.errors import RegistrationError
from app.modules.registration.schemas import (
    EnrolledResponse,
    ErrorResponse,
    RegistrationCreate,
    RegistrationListItem,
    TimetableItem,
    WaitlistedResponse,
)
from app.modules.registration.service import RegistrationService

router = APIRouter()


def registration_error_response(exc: RegistrationError) -> JSONResponse:
    return JSONResponse(
        status_code=int(exc.status_code),
        content=ErrorResponse(error=exc.code, message=exc.message).model_dump(),
    )


@router.post(
    "",
    response_model=EnrolledResponse | WaitlistedResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    status_code=status.HTTP_200_OK,
)
def create_registration(
    payload: RegistrationCreate,
    student_id: Annotated[int, Depends(get_current_student_id)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any] | JSONResponse:
    try:
        return RegistrationService(db).register(student_id, payload)
    except RegistrationError as exc:
        return registration_error_response(exc)


@router.delete(
    "/{enrollment_id}",
    response_model=None,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def delete_registration(
    enrollment_id: int,
    student_id: Annotated[int, Depends(get_current_student_id)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str | int] | JSONResponse:
    try:
        return RegistrationService(db).drop(student_id, enrollment_id)
    except RegistrationError as exc:
        return registration_error_response(exc)


@router.get("/me", response_model=list[RegistrationListItem])
def list_my_registrations(
    student_id: Annotated[int, Depends(get_current_student_id)],
    db: Annotated[Session, Depends(get_db)],
) -> list[RegistrationListItem]:
    return RegistrationService(db).list_current(student_id)


@router.get("/me/timetable", response_model=list[TimetableItem])
def get_my_timetable(
    student_id: Annotated[int, Depends(get_current_student_id)],
    db: Annotated[Session, Depends(get_db)],
) -> list[TimetableItem]:
    return RegistrationService(db).timetable(student_id)
