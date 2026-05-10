"""
Student profile service — get profile, update manual profile, re-sync INS.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.students.models import Student, StudentAcademicProfile, StudentCompletedCourse
from app.modules.students.schemas import (
    AcademicProfileOut,
    CompletedCourseOut,
    ManualProfileUpdateRequest,
    StudentProfileResponse,
)
from app.modules.sync.simple_scraper import run_sync_simple


def get_student_profile(db: Session, student: Student) -> StudentProfileResponse:
    profile = (
        db.query(StudentAcademicProfile)
        .filter(StudentAcademicProfile.student_id == student.id)
        .first()
    )
    courses = (
        db.query(StudentCompletedCourse)
        .filter(StudentCompletedCourse.student_id == student.id)
        .all()
    )
    gpa_rules_enabled = profile.gpa_is_verified if profile else False

    return StudentProfileResponse(
        student_number=student.student_number,
        full_name=student.full_name,
        profile_source=student.profile_source,
        gpa_rules_enabled=gpa_rules_enabled,
        academic_profile=AcademicProfileOut(
            department_name=profile.department_name if profile else None,
            major_name=profile.major_name if profile else None,
            academic_year=profile.academic_year if profile else None,
            current_gpa=profile.current_gpa if profile else None,
            gpa_is_verified=profile.gpa_is_verified if profile else False,
            academic_status=profile.academic_status if profile else None,
        )
        if profile
        else None,
        completed_courses=[
            CompletedCourseOut(
                course_code=c.course_code,
                course_title=c.course_title,
                grade=c.grade,
                credits=c.credits,
                source=c.source,
            )
            for c in courses
        ],
    )


def update_manual_profile(
    db: Session, student: Student, data: ManualProfileUpdateRequest
) -> StudentProfileResponse:
    if student.profile_source != "manual":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only manual-profile students can update their profile this way.",
        )

    profile = (
        db.query(StudentAcademicProfile)
        .filter(StudentAcademicProfile.student_id == student.id)
        .first()
    )
    if profile is None:
        profile = StudentAcademicProfile(student_id=student.id, gpa_is_verified=False)
        db.add(profile)

    profile.department_name = data.department_name
    profile.major_name = data.major_name
    profile.academic_year = data.academic_year
    profile.gpa_is_verified = False  # Never trust manually entered GPA
    db.flush()

    # Replace manual completed courses
    db.query(StudentCompletedCourse).filter(
        StudentCompletedCourse.student_id == student.id,
        StudentCompletedCourse.source == "manual",
    ).delete()
    for code in data.completed_course_codes:
        db.add(
            StudentCompletedCourse(
                student_id=student.id,
                course_code=code.upper().strip(),
                source="manual",
            )
        )
    db.commit()
    return get_student_profile(db, student)


def sync_ins_profile(db: Session, student: Student, password: str) -> StudentProfileResponse:
    """Re-sync INS data for an INS-verified student."""
    if student.profile_source != "ins_verified":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only INS-verified students can sync from INS.",
        )
    if student.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student user id is missing.",
        )

    try:
        run_sync_simple(db, str(student.user_id), student.student_number, password)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid INS credentials. Check your password.",
        ) from exc

    return get_student_profile(db, student)
