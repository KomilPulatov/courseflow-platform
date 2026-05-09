from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth import schemas, service

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/admin/login", response_model=schemas.TokenResponse)
def admin_login(body: schemas.AdminLoginRequest, db: DbSession) -> schemas.TokenResponse:
    return service.login_admin(db, body.email, body.password)


@router.post("/professor/login", response_model=schemas.TokenResponse)
def professor_login(body: schemas.ProfessorLoginRequest, db: DbSession) -> schemas.TokenResponse:
    return service.login_professor(db, body.email, body.password)


@router.post("/student/ins-login", response_model=schemas.INSLoginResponse)
def student_ins_login(body: schemas.INSLoginRequest, db: DbSession) -> schemas.INSLoginResponse:
    return service.login_student_ins(db, body.student_number, body.password)


@router.post("/student/manual-start", response_model=schemas.ManualStartResponse)
def student_manual_start(
    body: schemas.ManualStartRequest,
    db: DbSession,
) -> schemas.ManualStartResponse:
    return service.register_student_manual(
        db,
        body.student_number,
        body.full_name,
        body.email,
        body.password,
    )
