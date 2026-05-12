from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.curriculum_seed import seed_official_curricula
from app.db.models import AcademicProgram, Course, CurriculumCourse


def test_official_curricula_seed_creates_programs_and_shared_course_mappings(
    db_session: Session,
) -> None:
    seed_official_curricula(db_session)
    db_session.commit()

    rows = (
        db_session.query(AcademicProgram.code)
        .order_by(AcademicProgram.code)
        .all()
    )
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
