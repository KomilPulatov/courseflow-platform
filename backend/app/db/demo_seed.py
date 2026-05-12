from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.curriculum_seed import seed_official_curricula
from app.db.models import (
    Course,
    CourseOffering,
    CoursePrerequisite,
    Department,
    Major,
    Professor,
    RegistrationPeriod,
    Room,
    RoomAllocation,
    Section,
    SectionSchedule,
    Semester,
    Student,
    StudentAcademicProfile,
    StudentCompletedCourse,
    User,
)
from app.db.session import SessionLocal


def get_or_create_user(
    db: Session,
    *,
    email: str,
    password: str,
    role: str,
) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(email=email, password_hash=hash_password(password), role=role, status="active")
        db.add(user)
        db.flush()
    return user


def get_or_create_semester(db: Session, *, name: str, status: str) -> Semester:
    semester = db.query(Semester).filter(Semester.name == name).first()
    if semester is None:
        semester = Semester(name=name, status=status)
        db.add(semester)
        db.flush()
    return semester


def get_course(db: Session, *, code: str, title: str) -> Course:
    course = db.query(Course).filter(Course.code == code, Course.title == title).first()
    if course is None:
        raise LookupError(f"Course not found: {code} / {title}")
    return course


def ensure_prerequisite(db: Session, *, course_id: int, prerequisite_course_id: int) -> None:
    existing = (
        db.query(CoursePrerequisite)
        .filter(
            CoursePrerequisite.course_id == course_id,
            CoursePrerequisite.prerequisite_course_id == prerequisite_course_id,
        )
        .first()
    )
    if existing is None:
        db.add(
            CoursePrerequisite(
                course_id=course_id,
                prerequisite_course_id=prerequisite_course_id,
                rule_group="all",
            )
        )


def get_or_create_professor(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    department_name: str,
) -> Professor:
    user = get_or_create_user(db, email=email, password=password, role="professor")
    professor = db.query(Professor).filter(Professor.user_id == user.id).first()
    if professor is None:
        professor = Professor(
            user_id=user.id,
            full_name=full_name,
            department_name=department_name,
        )
        db.add(professor)
        db.flush()
    return professor


def get_or_create_student(
    db: Session,
    *,
    email: str,
    password: str,
    student_number: str,
    full_name: str,
    department: Department,
    major: Major,
    academic_year: int,
) -> Student:
    user = get_or_create_user(db, email=email, password=password, role="student")
    student = db.query(Student).filter(Student.user_id == user.id).first()
    if student is None:
        student = Student(
            user_id=user.id,
            student_number=student_number,
            full_name=full_name,
            profile_source="manual",
        )
        db.add(student)
        db.flush()

    profile = (
        db.query(StudentAcademicProfile)
        .filter(StudentAcademicProfile.student_id == student.id)
        .first()
    )
    if profile is None:
        profile = StudentAcademicProfile(student_id=student.id)
        db.add(profile)
        db.flush()

    profile.department_id = department.id
    profile.major_id = major.id
    profile.department_name = department.name
    profile.major_name = major.name
    profile.academic_year = academic_year
    profile.gpa_is_verified = False
    return student


def ensure_completed_course(db: Session, *, student_id: int, course: Course) -> None:
    existing = (
        db.query(StudentCompletedCourse)
        .filter(
            StudentCompletedCourse.student_id == student_id,
            StudentCompletedCourse.course_id == course.id,
        )
        .first()
    )
    if existing is None:
        db.add(
            StudentCompletedCourse(
                student_id=student_id,
                course_id=course.id,
                course_code=course.code,
                course_title=course.title,
                credits=course.credits,
                source="manual",
            )
        )


def get_or_create_offering(db: Session, *, course_id: int, semester_id: int) -> CourseOffering:
    offering = (
        db.query(CourseOffering)
        .filter(CourseOffering.course_id == course_id, CourseOffering.semester_id == semester_id)
        .first()
    )
    if offering is None:
        offering = CourseOffering(course_id=course_id, semester_id=semester_id, status="active")
        db.add(offering)
        db.flush()
    return offering


def get_or_create_section(
    db: Session,
    *,
    course_offering_id: int,
    professor_id: int | None,
    section_code: str,
    capacity: int,
    room_selection_mode: str,
    status: str,
) -> Section:
    section = (
        db.query(Section)
        .filter(
            Section.course_offering_id == course_offering_id,
            Section.section_code == section_code,
        )
        .first()
    )
    if section is None:
        section = Section(
            course_offering_id=course_offering_id,
            professor_id=professor_id,
            section_code=section_code,
            capacity=capacity,
            room_selection_mode=room_selection_mode,
            status=status,
        )
        db.add(section)
        db.flush()
    return section


def ensure_section_schedule(
    db: Session,
    *,
    section_id: int,
    day_of_week: str,
    start_time: str,
    end_time: str,
) -> None:
    existing = (
        db.query(SectionSchedule)
        .filter(
            SectionSchedule.section_id == section_id,
            SectionSchedule.day_of_week == day_of_week,
            SectionSchedule.start_time == start_time,
            SectionSchedule.end_time == end_time,
        )
        .first()
    )
    if existing is None:
        db.add(
            SectionSchedule(
                section_id=section_id,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
            )
        )


def get_or_create_room(
    db: Session,
    *,
    building: str,
    room_number: str,
    capacity: int,
    room_type: str = "lecture",
) -> Room:
    room = db.query(Room).filter(Room.building == building, Room.room_number == room_number).first()
    if room is None:
        room = Room(
            building=building,
            room_number=room_number,
            capacity=capacity,
            room_type=room_type,
            is_active=True,
        )
        db.add(room)
        db.flush()
    return room


def ensure_room_allocation(
    db: Session,
    *,
    section_id: int,
    room_id: int,
    admin_user_id: int,
    is_preferred: bool = False,
) -> RoomAllocation:
    existing = (
        db.query(RoomAllocation)
        .filter(RoomAllocation.section_id == section_id, RoomAllocation.room_id == room_id)
        .first()
    )
    if existing is None:
        existing = RoomAllocation(
            section_id=section_id,
            room_id=room_id,
            allocated_by_user_id=admin_user_id,
            is_preferred=is_preferred,
        )
        db.add(existing)
        db.flush()
    return existing


def ensure_registration_period(db: Session, *, semester_id: int) -> None:
    now = datetime.now(UTC)
    existing = (
        db.query(RegistrationPeriod)
        .filter(
            RegistrationPeriod.semester_id == semester_id,
            RegistrationPeriod.opens_at < now + timedelta(days=30),
            RegistrationPeriod.closes_at > now - timedelta(days=30),
        )
        .first()
    )
    if existing is None:
        db.add(
            RegistrationPeriod(
                semester_id=semester_id,
                opens_at=now - timedelta(days=1),
                closes_at=now + timedelta(days=30),
                status="open",
            )
        )


def seed_demo_data() -> None:
    db = SessionLocal()
    try:
        seed_official_curricula(db)
        admin = get_or_create_user(
            db,
            email="admin@crsp.example.com",
            password="admin12345",
            role="admin",
        )
        semester = get_or_create_semester(db, name="Spring 2026", status="active")
        socie = db.query(Department).filter(Department.code == "SOCIE").one()
        cse_major = db.query(Major).filter(Major.code == "CSE").one()
        professor = get_or_create_professor(
            db,
            email="professor@crsp.example.com",
            password="prof12345",
            full_name="Dr. Demo Professor",
            department_name=socie.name,
        )
        student = get_or_create_student(
            db,
            email="student@crsp.example.com",
            password="student12345",
            student_number="2310204",
            full_name="Demo Student",
            department=socie,
            major=cse_major,
            academic_year=3,
        )

        oop_1 = get_course(db, code="MSC1051", title="Object-Oriented Programming 1")
        oop_2 = get_course(db, code="MSC1052", title="Object-Oriented Programming 2")
        database_core = get_course(db, code="SOC3020", title="Database")
        database_design = get_course(db, code="SOC3060", title="Database Application & Design")

        ensure_prerequisite(db, course_id=oop_2.id, prerequisite_course_id=oop_1.id)
        ensure_prerequisite(db, course_id=database_core.id, prerequisite_course_id=oop_2.id)
        ensure_prerequisite(
            db, course_id=database_design.id, prerequisite_course_id=database_core.id
        )

        ensure_completed_course(db, student_id=student.id, course=oop_1)
        ensure_completed_course(db, student_id=student.id, course=oop_2)
        ensure_completed_course(db, student_id=student.id, course=database_core)

        databases_offering = get_or_create_offering(
            db,
            course_id=database_design.id,
            semester_id=semester.id,
        )
        section_001 = get_or_create_section(
            db,
            course_offering_id=databases_offering.id,
            professor_id=professor.id,
            section_code="001",
            capacity=30,
            room_selection_mode="professor_choice",
            status="open",
        )
        section_002 = get_or_create_section(
            db,
            course_offering_id=databases_offering.id,
            professor_id=professor.id,
            section_code="002",
            capacity=24,
            room_selection_mode="admin_fixed",
            status="open",
        )

        ensure_section_schedule(
            db,
            section_id=section_001.id,
            day_of_week="Monday",
            start_time="09:00",
            end_time="10:30",
        )
        ensure_section_schedule(
            db,
            section_id=section_002.id,
            day_of_week="Wednesday",
            start_time="13:00",
            end_time="14:30",
        )

        room_a101 = get_or_create_room(
            db, building="A", room_number="101", capacity=40, room_type="lecture"
        )
        room_a102 = get_or_create_room(
            db, building="A", room_number="102", capacity=25, room_type="lecture"
        )
        room_b201 = get_or_create_room(
            db, building="B", room_number="201", capacity=35, room_type="lab"
        )

        ensure_room_allocation(
            db,
            section_id=section_001.id,
            room_id=room_a101.id,
            admin_user_id=admin.id,
        )
        ensure_room_allocation(
            db,
            section_id=section_001.id,
            room_id=room_a102.id,
            admin_user_id=admin.id,
        )
        ensure_room_allocation(
            db,
            section_id=section_002.id,
            room_id=room_b201.id,
            admin_user_id=admin.id,
            is_preferred=True,
        )

        ensure_registration_period(db, semester_id=semester.id)

        db.commit()
        print("Demo seed complete.")
        print(f"Admin login: {admin.email} / admin12345")
        print("Professor login: professor@crsp.example.com / prof12345")
        print("Student login: student@crsp.example.com / student12345")
    except OperationalError as exc:
        raise SystemExit(
            "Database schema is missing. "
            "Run `uv run alembic upgrade head` before seeding demo data."
        ) from exc
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
