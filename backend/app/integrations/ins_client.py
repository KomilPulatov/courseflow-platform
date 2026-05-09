from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class InsCompletedCourse:
    code: str
    title: str
    grade: str
    credits: int


@dataclass(frozen=True)
class InsStudentProfile:
    student_number: str
    full_name: str
    department: str
    major: str
    academic_year: int
    current_gpa: float
    academic_status: str
    completed_courses: tuple[InsCompletedCourse, ...]


def verify_ins_credentials(student_number: str, password: str) -> InsStudentProfile | None:
    if not settings.INS_MOCK_ENABLED:
        return None
    if password != student_number:
        return None

    return InsStudentProfile(
        student_number=student_number,
        full_name=f"INS Student {student_number}",
        department="ICE",
        major="Information and Computer Engineering",
        academic_year=3,
        current_gpa=4.2,
        academic_status="active",
        completed_courses=(
            InsCompletedCourse(
                code="CSE2010",
                title="Programming",
                grade="A",
                credits=3,
            ),
        ),
    )
