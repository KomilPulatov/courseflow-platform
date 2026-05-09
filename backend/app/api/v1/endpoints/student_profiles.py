from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_student
from app.modules.students import schemas, service
from app.modules.students.models import Student

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
    student: Student = Depends(get_current_student),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """Re-sync profile data from INS. Only for ins_verified students."""
    return service.sync_ins_profile(db, student)
