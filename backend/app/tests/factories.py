from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models import (
    Course,
    CourseEligibilityRule,
    CourseOffering,
    CoursePrerequisite,
    RegistrationPeriod,
    Section,
    SectionSchedule,
    Semester,
    Student,
    StudentAcademicProfile,
    StudentCompletedCourse,
)


def seed_registration_case(
    db: Session,
    *,
    student_id: int = 1,
    section_capacity: int = 2,
    with_gpa_rule: bool = False,
    with_prerequisite: bool = False,
) -> dict[str, int]:
    now = datetime.now(UTC)
    student = Student(
        id=student_id,
        student_number=f"2310{student_id:03d}",
        full_name="Demo Student",
        profile_source="manual",
    )
    profile = StudentAcademicProfile(
        student_id=student_id,
        department_id=1,
        major_id=1,
        academic_year=3,
        gpa_is_verified=False,
    )
    semester = Semester(id=1, name="Spring 2026", status="active")
    course = Course(id=1, department_id=1, code="CSE3010", title="Databases", credits=3)
    offering = CourseOffering(id=1, course_id=1, semester_id=1, status="active")
    section = Section(
        id=1,
        course_offering_id=1,
        section_code="001",
        capacity=section_capacity,
        status="open",
    )
    period = RegistrationPeriod(
        id=1,
        semester_id=1,
        opens_at=now - timedelta(days=1),
        closes_at=now + timedelta(days=1),
        status="open",
    )
    schedule = SectionSchedule(
        id=1,
        section_id=1,
        day_of_week="Monday",
        start_time="09:00",
        end_time="10:30",
    )
    db.add_all([student, profile, semester, course, offering, section, period, schedule])
    if with_gpa_rule:
        db.add(CourseEligibilityRule(course_id=1, min_gpa=3.5))
    if with_prerequisite:
        prerequisite = Course(
            id=2,
            department_id=1,
            code="CSE2010",
            title="Programming",
            credits=3,
        )
        db.add(prerequisite)
        db.flush()
        db.add(CoursePrerequisite(course_id=1, prerequisite_course_id=2))
        db.add(
            StudentCompletedCourse(
                student_id=student_id,
                course_id=2,
                course_code="CSE2010",
                source="manual",
            )
        )
    db.commit()
    return {"student_id": student_id, "section_id": 1}
