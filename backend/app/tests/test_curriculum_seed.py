from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.db.curriculum_seed import seed_official_curricula
from app.db.demo_seed import get_or_create_student
from app.db.models import (
    AcademicProgram,
    Course,
    CourseEquivalency,
    CurriculumCourse,
    Department,
    Major,
    Student,
)


def test_official_curricula_seed_creates_programs_and_shared_course_mappings(
    db_session: Session,
) -> None:
    seed_official_curricula(db_session)
    db_session.commit()

    rows = db_session.query(AcademicProgram.code).order_by(AcademicProgram.code).all()
    program_codes = {code for (code,) in rows}
    assert program_codes == {"BA", "CSE", "ICE", "SBL"}

    course_count = db_session.query(func.count(Course.id)).scalar()
    assert course_count is not None
    assert course_count > 100

    database_course = (
        db_session.query(Course).filter(Course.code == "SOC3020", Course.title == "Database").one()
    )
    mappings = (
        db_session.query(CurriculumCourse)
        .filter(CurriculumCourse.course_id == database_course.id)
        .all()
    )
    mapped_program_codes = {
        db_session.get(AcademicProgram, mapping.program_id).code for mapping in mappings
    }
    assert mapped_program_codes == {"CSE", "ICE"}


def test_conflicting_course_codes_are_kept_as_distinct_courses(db_session: Session) -> None:
    seed_official_curricula(db_session)
    db_session.commit()

    nts4060_courses = (
        db_session.query(Course).filter(Course.code == "NTS4060").order_by(Course.title).all()
    )

    assert [course.title for course in nts4060_courses] == [
        "Distinguished Lecture in Social Science and Art",
        "International Commercial Law",
    ]


def test_official_curricula_seed_creates_cross_program_equivalencies(db_session: Session) -> None:
    seed_official_curricula(db_session)
    db_session.commit()

    ice_intro = (
        db_session.query(Course)
        .filter(Course.code == "ICE1010", Course.title == "Introduction to IT")
        .one()
    )
    cse_intro = (
        db_session.query(Course)
        .filter(Course.code == "CSE1010", Course.title == "Introduction to IT")
        .one()
    )
    intro_to_it_pairs = (
        db_session.query(CourseEquivalency)
        .filter(
            or_(
                CourseEquivalency.course_id == ice_intro.id,
                CourseEquivalency.equivalent_course_id == ice_intro.id,
            )
        )
        .all()
    )

    assert intro_to_it_pairs

    assert any(
        {
            pair.course_id,
            pair.equivalent_course_id,
        }
        == {ice_intro.id, cse_intro.id}
        and pair.equivalence_type == "cross_program"
        for pair in intro_to_it_pairs
    )


def test_demo_student_seed_reuses_existing_student_number_with_new_login(
    db_session: Session,
) -> None:
    seed_official_curricula(db_session)
    department = db_session.query(Department).filter(Department.code == "SOCIE").one()
    major = db_session.query(Major).filter(Major.code == "CSE").one()

    legacy_student = Student(
        student_number="2310204",
        full_name="Legacy Demo Student",
        profile_source="manual",
    )
    db_session.add(legacy_student)
    db_session.commit()

    seeded_student = get_or_create_student(
        db_session,
        email="student@crsp.example.com",
        password="student12345",
        student_number="2310204",
        full_name="Demo Student",
        department=department,
        major=major,
        academic_year=3,
    )
    db_session.commit()

    students = db_session.query(Student).filter(Student.student_number == "2310204").all()
    assert len(students) == 1
    assert seeded_student.id == legacy_student.id
    assert seeded_student.user_id is not None
    assert seeded_student.full_name == "Demo Student"
