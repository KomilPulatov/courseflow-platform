from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_student_id
from app.db.session import get_db
from app.modules.registration.errors import RegistrationError
from app.modules.registration.schemas import EligibilityResponse, ErrorResponse
from app.modules.registration.service import RegistrationService

router = APIRouter()


def registration_error_response(exc: RegistrationError) -> JSONResponse:
    return JSONResponse(
        status_code=int(exc.status_code),
        content=ErrorResponse(error=exc.code, message=exc.message).model_dump(),
    )


@router.get(
    "/{section_id}/eligibility",
    response_model=EligibilityResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_section_eligibility(
    section_id: int,
    student_id: Annotated[int, Depends(get_current_student_id)],
    db: Annotated[Session, Depends(get_db)],
) -> EligibilityResponse | JSONResponse:
    try:
        return RegistrationService(db).preview_eligibility(student_id, section_id)
    except RegistrationError as exc:
        return registration_error_response(exc)
