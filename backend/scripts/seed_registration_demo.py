from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import (
    AuditLog,
    Course,
    CourseOffering,
    Enrollment,
    RegistrationEvent,
    RegistrationIdempotencyKey,
    RegistrationPeriod,
    Section,
    SectionSchedule,
    Semester,
    Student,
    StudentAcademicProfile,
    WaitlistEntry,
)
from app.db.session import SessionLocal, engine

COURSE_CODE = "DEMO-RW101"
SEMESTER_NAME = "Demo Spring 2026"
SECTION_CODE = "RW-001"
STUDENT_NUMBERS = ("DEMO-RW-001", "DEMO-RW-002", "DEMO-RW-003")


def main() -> None:
    # The demo script is intentionally repeatable for classroom presentations.
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        semester = upsert_semester(db)
        course = upsert_course(db)
        offering = upsert_offering(db, course, semester)
        section = upsert_section(db, offering)
        upsert_period(db, semester)
        upsert_schedule(db, section)
        students = [
            upsert_student(db, number, index)
            for index, number in enumerate(STUDENT_NUMBERS)
        ]
        reset_demo_state(db, section, students)
        section_id = section.id
        student_rows = [
            (student.id, student.student_number, student.full_name) for student in students
        ]
        db.commit()
    finally:
        db.close()

    print("Registration demo data is ready.")
    print(f"Section id: {section_id} ({COURSE_CODE} / {SECTION_CODE}, capacity 1)")
    print("Use these X-Student-Id values in Swagger:")
    for student_id, student_number, full_name in student_rows:
        print(f"- {student_id}: {student_number} / {full_name}")
    print("Demo flow:")
    print("1. Student 1 POST /api/v1/registrations and takes the only seat.")
    print("2. Student 2 POST /api/v1/registrations and is waitlisted.")
    print("3. Student 2 GET /api/v1/waitlists/me to see position 1.")
    print("4. Student 1 DELETE /api/v1/registrations/{enrollment_id}.")
    print("5. Student 2 is promoted automatically.")


def upsert_semester(db: Session) -> Semester:
    semester = db.query(Semester).filter_by(name=SEMESTER_NAME).first()
    if semester is None:
        semester = Semester(name=SEMESTER_NAME, status="active")
        db.add(semester)
        db.flush()
    else:
        semester.status = "active"
    return semester


def upsert_course(db: Session) -> Course:
    course = db.query(Course).filter_by(code=COURSE_CODE).first()
    if course is None:
        course = Course(
            department_id=1,
            code=COURSE_CODE,
            title="Registration and Waitlist Demo",
            credits=3,
        )
        db.add(course)
        db.flush()
    else:
        course.department_id = 1
        course.title = "Registration and Waitlist Demo"
        course.credits = 3
    return course


def upsert_offering(db: Session, course: Course, semester: Semester) -> CourseOffering:
    offering = (
        db.query(CourseOffering)
        .filter_by(course_id=course.id, semester_id=semester.id)
        .first()
    )
    if offering is None:
        offering = CourseOffering(course_id=course.id, semester_id=semester.id, status="active")
        db.add(offering)
        db.flush()
    else:
        offering.status = "active"
    return offering


def upsert_section(db: Session, offering: CourseOffering) -> Section:
    section = (
        db.query(Section)
        .filter_by(course_offering_id=offering.id, section_code=SECTION_CODE)
        .first()
    )
    if section is None:
        section = Section(
            course_offering_id=offering.id,
            section_code=SECTION_CODE,
            capacity=1,
            status="open",
        )
        db.add(section)
        db.flush()
    else:
        section.capacity = 1
        section.status = "open"
    return section


def upsert_period(db: Session, semester: Semester) -> None:
    now = datetime.now(UTC)
    period = db.query(RegistrationPeriod).filter_by(semester_id=semester.id).first()
    if period is None:
        db.add(
            RegistrationPeriod(
                semester_id=semester.id,
                opens_at=now - timedelta(days=1),
                closes_at=now + timedelta(days=7),
                status="open",
            )
        )
    else:
        period.opens_at = now - timedelta(days=1)
        period.closes_at = now + timedelta(days=7)
        period.status = "open"


def upsert_schedule(db: Session, section: Section) -> None:
    schedule = db.query(SectionSchedule).filter_by(section_id=section.id).first()
    if schedule is None:
        db.add(
            SectionSchedule(
                section_id=section.id,
                day_of_week="Monday",
                start_time="09:00",
                end_time="10:30",
            )
        )
    else:
        schedule.day_of_week = "Monday"
        schedule.start_time = "09:00"
        schedule.end_time = "10:30"


def upsert_student(db: Session, student_number: str, index: int) -> Student:
    student = db.query(Student).filter_by(student_number=student_number).first()
    if student is None:
        student = Student(
            student_number=student_number,
            full_name=f"Demo Waitlist Student {index + 1}",
            profile_source="manual",
        )
        db.add(student)
        db.flush()
    else:
        student.full_name = f"Demo Waitlist Student {index + 1}"
        student.profile_source = "manual"

    profile = db.query(StudentAcademicProfile).filter_by(student_id=student.id).first()
    if profile is None:
        db.add(
            StudentAcademicProfile(
                student_id=student.id,
                department_id=1,
                major_id=1,
                academic_year=3,
                gpa_is_verified=False,
            )
        )
    else:
        profile.department_id = 1
        profile.major_id = 1
        profile.academic_year = 3
        profile.gpa_is_verified = False
    return student


def reset_demo_state(db: Session, section: Section, students: list[Student]) -> None:
    # Clear only the generated demo activity, not the whole database.
    student_ids = [student.id for student in students]
    db.query(WaitlistEntry).filter(WaitlistEntry.section_id == section.id).delete(
        synchronize_session=False
    )
    db.query(Enrollment).filter(Enrollment.section_id == section.id).delete(
        synchronize_session=False
    )
    db.query(RegistrationIdempotencyKey).filter(
        RegistrationIdempotencyKey.student_id.in_(student_ids)
    ).delete(synchronize_session=False)
    db.query(RegistrationEvent).filter(RegistrationEvent.section_id == section.id).delete(
        synchronize_session=False
    )
    db.query(AuditLog).filter(AuditLog.actor_student_id.in_(student_ids)).delete(
        synchronize_session=False
    )


if __name__ == "__main__":
    main()
