from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_student
from app.modules.students import schemas, service
from app.modules.students.models import Student, StudentAcademicProfile, StudentCompletedCourse
from app.modules.sync.schemas import (
    TranscriptCourseOut,
    TranscriptResponse,
    TranscriptStudentOut,
)

router = APIRouter()


@router.get("/me", response_model=schemas.StudentProfileResponse)
def get_my_profile(
    student: Student = Depends(get_current_student),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """Get current student's full profile including completed courses and GPA status."""
    return service.get_student_profile(db, student)


@router.put("/me/manual", response_model=schemas.StudentProfileResponse)
def update_manual_profile(
    body: schemas.ManualProfileUpdateRequest,
    student: Student = Depends(get_current_student),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Complete or update a manual student profile.
    Only for manual profile students. gpa is never accepted.
    Provide department, major, year, and list of completed courses
    """
    return service.update_manual_profile(db, student, body)


@router.post("/me/sync-ins", response_model=schemas.StudentProfileResponse)
def sync_ins(
    body: schemas.INSSyncRequest,
    student: Student = Depends(get_current_student),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """Re-sync profile data from INS. Only for ins_verified students."""
    return service.sync_ins_profile(db, student, body.password)


@router.get("/{user_id}/transcript", response_model=TranscriptResponse)
def get_transcript(
    user_id: str,
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Return the latest canonical transcript for a student (by internal user_id).

    Includes: student identity, cumulative + per-semester GPA, all completed courses.
    """
    student: Student | None = db.query(Student).filter(Student.user_id == int(user_id)).first()
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    profile: StudentAcademicProfile | None = (
        db.query(StudentAcademicProfile)
        .filter(StudentAcademicProfile.student_id == student.id)
        .first()
    )

    courses = (
        db.query(StudentCompletedCourse)
        .filter(
            StudentCompletedCourse.student_id == student.id,
            StudentCompletedCourse.source == "ins_verified",
        )
        .all()
    )

    cumulative_gpa = float(profile.current_gpa) if profile and profile.current_gpa else 0.0

    return TranscriptResponse(
        student=TranscriptStudentOut(
            student_number=student.student_number,
            full_name=student.full_name,
            department_name=profile.department_name if profile else "",
            major_name=profile.major_name if profile else "",
            year_standing=str(profile.academic_year) if profile else "",
            cumulative_gpa=cumulative_gpa,
        ),
        gpa={
            "cumulative": cumulative_gpa,
            "semester": [],  # populated from GPA records if stored separately
        },
        courses=[
            TranscriptCourseOut(
                external_id=f"{student.student_number}::{c.course_code}",
                semester="",
                code=c.course_code,
                title=c.course_title or "",
                credits=c.credits or 0,
                grade=c.grade or "",
                grade_points=0.0,
            )
            for c in courses
        ],
    )
