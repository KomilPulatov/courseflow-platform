"""
Auth service — login business logic for all three roles.
"""

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    INSLoginResponse,
    ManualStartResponse,
    TokenResponse,
)
from app.modules.students.models import ExternalAccount, Student, StudentAcademicProfile
from app.modules.sync.simple_scraper import run_sync_simple

# Admin login


def login_admin(db: Session, email: str, password: str) -> TokenResponse:
    user = db.query(User).filter(User.email == email, User.role == "admin").first()
    if not user or not verify_password(password, user.password_hash or ""):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user.id, "admin")
    return TokenResponse(access_token=token, role="admin")


# ---------------------------------------------------------------------------
# Professor login


def login_professor(db: Session, email: str, password: str) -> TokenResponse:
    user = db.query(User).filter(User.email == email, User.role == "professor").first()
    if not user or not verify_password(password, user.password_hash or ""):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user.id, "professor")
    return TokenResponse(access_token=token, role="professor")


# Student — INS login


def login_student_ins(db: Session, student_number: str, password: str) -> INSLoginResponse:
    # 1. Upsert User (INS students may not have an email)
    student = db.query(Student).filter(Student.student_number == student_number).first()
    if student is None:
        user = User(role="student")
        db.add(user)
        db.flush()

        student = Student(
            user_id=user.id,
            student_number=student_number,
            full_name=student_number,
            profile_source="ins_verified",
        )
        db.add(student)
        db.flush()
    else:
        student.profile_source = "ins_verified"
        user = db.query(User).filter(User.id == student.user_id).first()

        if user is None:
            user = User(role="student")
            db.add(user)
            db.flush()
            student.user_id = user.id
    try:
        run_sync_simple(db, str(user.id), student_number, password)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid INS credentials. Check your student number and password.",
        ) from exc

    db.refresh(student)
    profile = (
        db.query(StudentAcademicProfile)
        .filter(StudentAcademicProfile.student_id == student.id)
        .first()
    )

    now = datetime.now(UTC)

    # 5. Upsert ExternalAccount
    ext = (
        db.query(ExternalAccount)
        .filter(
            ExternalAccount.student_id == student.id,
            ExternalAccount.provider == "ins",
        )
        .first()
    )
    if ext is None:
        db.add(
            ExternalAccount(
                student_id=student.id,
                provider="ins",
                external_user_id=student_number,
                last_verified_at=now,
            )
        )
    else:
        ext.last_verified_at = now

    db.commit()

    token = create_access_token(user.id, "student")
    return INSLoginResponse(
        access_token=token,
        student_number=student.student_number,
        full_name=student.full_name,
        department=profile.department_name if profile else "",
        major=profile.major_name if profile else "",
        current_gpa=float(profile.current_gpa) if profile and profile.current_gpa else 0.0,
    )


# Student — Manual start


def register_student_manual(
    db: Session, student_number: str, full_name: str, email: str, password: str
) -> ManualStartResponse:
    # Check student_number uniqueness
    existing = db.query(Student).filter(Student.student_number == student_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this student number already exists.",
        )

    # Check email uniqueness
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(email=email, password_hash=hash_password(password), role="student")
    db.add(user)
    db.flush()

    student = Student(
        user_id=user.id,
        student_number=student_number,
        full_name=full_name,
        profile_source="manual",
    )
    db.add(student)
    db.flush()

    # Create empty academic profile (student fills it in next step)
    db.add(
        StudentAcademicProfile(
            student_id=student.id,
            gpa_is_verified=False,  # manual — GPA never trusted
        )
    )
    db.commit()

    token = create_access_token(user.id, "student")
    return ManualStartResponse(access_token=token)
