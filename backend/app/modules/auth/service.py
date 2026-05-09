"""
Auth service — login business logic for all three roles.
"""

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.integrations.ins_client import verify_ins_credentials
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    INSLoginResponse,
    ManualStartResponse,
    TokenResponse,
)
from app.modules.students.models import (
    ExternalAccount,
    Student,
    StudentAcademicProfile,
    StudentCompletedCourse,
)

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
    # 1. Verify against INS
    ins_data = verify_ins_credentials(student_number, password)
    if ins_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid INS credentials. Check your student number and password.",
        )

    # 2. Upsert User (INS students may not have an email)
    student = db.query(Student).filter(Student.student_number == student_number).first()
    if student is None:
        user = User(role="student")
        db.add(user)
        db.flush()  # get user.id

        student = Student(
            user_id=user.id,
            student_number=ins_data.student_number,
            full_name=ins_data.full_name,
            profile_source="ins_verified",
        )
        db.add(student)
        db.flush()
    else:
        # Update name in case it changed
        student.full_name = ins_data.full_name
        student.profile_source = "ins_verified"
        user = db.query(User).filter(User.id == student.user_id).first()

    # 3. Upsert AcademicProfile
    profile = (
        db.query(StudentAcademicProfile)
        .filter(StudentAcademicProfile.student_id == student.id)
        .first()
    )
    now = datetime.now(UTC)
    if profile is None:
        profile = StudentAcademicProfile(
            student_id=student.id,
            department_name=ins_data.department,
            major_name=ins_data.major,
            academic_year=ins_data.academic_year,
            current_gpa=ins_data.current_gpa,
            gpa_is_verified=True,  # INS data is trusted
            academic_status=ins_data.academic_status,
            last_synced_at=now,
        )
        db.add(profile)
    else:
        profile.department_name = ins_data.department
        profile.major_name = ins_data.major
        profile.academic_year = ins_data.academic_year
        profile.current_gpa = ins_data.current_gpa
        profile.gpa_is_verified = True
        profile.academic_status = ins_data.academic_status
        profile.last_synced_at = now

    db.flush()

    # 4. Sync completed courses (replace all ins_verified ones)
    db.query(StudentCompletedCourse).filter(
        StudentCompletedCourse.student_id == student.id,
        StudentCompletedCourse.source == "ins_verified",
    ).delete()
    for course in ins_data.completed_courses:
        db.add(
            StudentCompletedCourse(
                student_id=student.id,
                course_code=course.code,
                course_title=course.title,
                grade=course.grade,
                credits=course.credits,
                source="ins_verified",
            )
        )

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
        student_number=ins_data.student_number,
        full_name=ins_data.full_name,
        department=ins_data.department,
        major=ins_data.major,
        current_gpa=ins_data.current_gpa,
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
