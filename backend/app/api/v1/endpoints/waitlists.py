from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_student_id
from app.db.session import get_db
from app.modules.registration.errors import RegistrationError
from app.modules.registration.schemas import (
    ErrorResponse,
    WaitlistCancelResponse,
    WaitlistCreate,
    WaitlistedResponse,
    WaitlistItem,
)
from app.modules.registration.service import RegistrationService

router = APIRouter()


def registration_error_response(exc: RegistrationError) -> JSONResponse:
    # Keep business-rule errors in the same JSON shape as the registration routes.
    return JSONResponse(
        status_code=int(exc.status_code),
        content=ErrorResponse(error=exc.code, message=exc.message).model_dump(),
    )


@router.get("/me", response_model=list[WaitlistItem])
def list_my_waitlist(
    student_id: Annotated[int, Depends(get_current_student_id)],
    db: Annotated[Session, Depends(get_db)],
) -> list[WaitlistItem]:
    return RegistrationService(db).list_waitlist(student_id)


@router.post(
    "",
    response_model=WaitlistedResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    status_code=status.HTTP_200_OK,
)
def join_waitlist(
    payload: WaitlistCreate,
    student_id: Annotated[int, Depends(get_current_student_id)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any] | JSONResponse:
    # The service does the actual capacity and eligibility checks inside a transaction.
    try:
        return RegistrationService(db).join_waitlist(student_id, payload)
    except RegistrationError as exc:
        return registration_error_response(exc)


@router.delete(
    "/{entry_id}",
    response_model=WaitlistCancelResponse,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def cancel_waitlist(
    entry_id: int,
    student_id: Annotated[int, Depends(get_current_student_id)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str | int] | JSONResponse:
    try:
        return RegistrationService(db).cancel_waitlist(student_id, entry_id)
    except RegistrationError as exc:
        return registration_error_response(exc)
