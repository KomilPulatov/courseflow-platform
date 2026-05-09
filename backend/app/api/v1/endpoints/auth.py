from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth import schemas, service

router = APIRouter()


@router.post("/admin/login", response_model=schemas.TokenResponse)
def admin_login(body: schemas.AdminLoginRequest, db: Session = Depends(get_db)):
    """Admin login with email + password."""
    return service.login_admin(db, body.email, body.password)


@router.post("/professor/login", response_model=schemas.TokenResponse)
def professor_login(body: schemas.ProfessorLoginRequest, db: Session = Depends(get_db)):
    """Professor login with email + password."""
    return service.login_professor(db, body.email, body.password)


@router.post("/student/ins-login", response_model=schemas.INSLoginResponse)
def student_ins_login(body: schemas.INSLoginRequest, db: Session = Depends(get_db)):
    """
    Student login via IUT INS.
    Syncs academic data (GPA, courses) from INS — gpa_is_verified=True.
    Demo: use student_number as password, e.g. U2310037 / U2310037
    """
    return service.login_student_ins(db, body.student_number, body.password)


@router.post("/student/manual-start", response_model=schemas.ManualStartResponse)
def student_manual_start(body: schemas.ManualStartRequest, db: Session = Depends(get_db)):
    """
    Create a manual student account.
    GPA will never be trusted (gpa_is_verified=False).
    After this, call PUT /student-profiles/me/manual to complete the profile.
    """
    return service.register_student_manual(
        db, body.student_number, body.full_name, body.email, body.password
    )
