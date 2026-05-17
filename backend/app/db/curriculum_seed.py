from sqlalchemy.orm import Session

from app.db.curriculum_seed_data import CURRICULA, EQUIVALENCIES, PROGRAMS
from app.db.models import (
    AcademicProgram,
    Course,
    CourseEquivalency,
    CurriculumCourse,
    Department,
    Major,
)
from app.db.session import SessionLocal

DEPARTMENTS = {
    "COMMON": "Common Curriculum",
    "SOCIE": "School of Computer Science and Information Engineering",
    "BUSLOG": "School of Business and Logistics",
}

MAJORS = {
    "ICE": {"department_code": "SOCIE", "name": "Information and Communication Engineering"},
    "CSE": {"department_code": "SOCIE", "name": "Computer Science and Software Engineering"},
    "BA": {"department_code": "BUSLOG", "name": "Business Administration"},
    "SBL": {"department_code": "BUSLOG", "name": "Logistics Management"},
}

COURSE_TITLE_OVERRIDES = {
    "MSC1051": "Object-Oriented Programming 1",
}


def course_department_code(course_code: str) -> str:
    if course_code.startswith(("GEN", "NTS", "MSC")):
        return "COMMON"
    if course_code.startswith(("ICE", "SOC", "CSE")):
        return "SOCIE"
    if course_code.startswith(("TSF", "TSL", "TSM", "TSE", "TSN", "TSI")):
        return "BUSLOG"
    return "COMMON"


def get_or_create_department(db: Session, *, code: str, name: str) -> Department:
    department = db.query(Department).filter(Department.code == code).first()
    if department is None:
        department = Department(code=code, name=name)
        db.add(department)
        db.flush()
    return department


def get_or_create_program(
    db: Session,
    *,
    department_id: int,
    code: str,
    name: str,
) -> AcademicProgram:
    program = db.query(AcademicProgram).filter(AcademicProgram.code == code).first()
    if program is None:
        program = AcademicProgram(
            department_id=department_id,
            code=code,
            name=name,
            degree_level="undergraduate",
        )
        db.add(program)
        db.flush()
    return program


def get_or_create_major(
    db: Session,
    *,
    department_id: int,
    code: str,
    name: str,
) -> Major:
    major = db.query(Major).filter(Major.department_id == department_id, Major.code == code).first()
    if major is None:
        major = Major(department_id=department_id, code=code, name=name)
        db.add(major)
        db.flush()
    return major


def get_or_create_course(
    db: Session,
    *,
    department_id: int,
    code: str,
    title: str,
    credits: int,
) -> Course:
    canonical_title = COURSE_TITLE_OVERRIDES.get(code, title)
    course = (
        db.query(Course)
        .filter(
            Course.code == code,
            Course.title == canonical_title,
            Course.credits == credits,
        )
        .first()
    )
    if course is None:
        course = Course(
            department_id=department_id,
            code=code,
            title=canonical_title,
            credits=credits,
            course_type=None,
            description=None,
            is_repeatable=False,
        )
        db.add(course)
        db.flush()
    return course


def get_or_create_curriculum_course(
    db: Session,
    *,
    program_id: int,
    course_id: int,
    category: str,
    is_mandatory: bool,
) -> CurriculumCourse:
    curriculum_course = (
        db.query(CurriculumCourse)
        .filter(
            CurriculumCourse.program_id == program_id,
            CurriculumCourse.course_id == course_id,
        )
        .first()
    )
    if curriculum_course is None:
        curriculum_course = CurriculumCourse(
            program_id=program_id,
            course_id=course_id,
            category=category,
            is_mandatory=is_mandatory,
        )
        db.add(curriculum_course)
        db.flush()
    else:
        curriculum_course.category = category
        curriculum_course.is_mandatory = is_mandatory
    return curriculum_course


def get_or_create_course_equivalency(
    db: Session,
    *,
    left_course_id: int,
    right_course_id: int,
    equivalence_type: str,
) -> CourseEquivalency:
    low_id = min(left_course_id, right_course_id)
    high_id = max(left_course_id, right_course_id)
    equivalency = (
        db.query(CourseEquivalency)
        .filter(
            CourseEquivalency.course_id == low_id,
            CourseEquivalency.equivalent_course_id == high_id,
        )
        .first()
    )
    if equivalency is None:
        equivalency = CourseEquivalency(
            course_id=low_id,
            equivalent_course_id=high_id,
            equivalence_type=equivalence_type,
        )
        db.add(equivalency)
        db.flush()
    else:
        equivalency.equivalence_type = equivalence_type
    return equivalency


def seed_official_curricula(db: Session) -> None:
    departments = {
        code: get_or_create_department(db, code=code, name=name)
        for code, name in DEPARTMENTS.items()
    }

    programs = {
        code: get_or_create_program(
            db,
            department_id=departments[data["department_code"]].id,
            code=code,
            name=data["name"],
        )
        for code, data in PROGRAMS.items()
    }

    for code, data in MAJORS.items():
        get_or_create_major(
            db,
            department_id=departments[data["department_code"]].id,
            code=code,
            name=data["name"],
        )

    for program_code, entries in CURRICULA.items():
        program = programs[program_code]
        for category, course_code, title, credits, is_mandatory in entries:
            department = departments[course_department_code(course_code)]
            course = get_or_create_course(
                db,
                department_id=department.id,
                code=course_code,
                title=title,
                credits=credits,
            )
            get_or_create_curriculum_course(
                db,
                program_id=program.id,
                course_id=course.id,
                category=category,
                is_mandatory=is_mandatory,
            )

    for (
        left_code,
        left_title,
        left_credits,
        right_code,
        right_title,
        right_credits,
        equivalence_type,
    ) in EQUIVALENCIES:
        left_course = get_or_create_course(
            db,
            department_id=departments[course_department_code(left_code)].id,
            code=left_code,
            title=left_title,
            credits=left_credits,
        )
        right_course = get_or_create_course(
            db,
            department_id=departments[course_department_code(right_code)].id,
            code=right_code,
            title=right_title,
            credits=right_credits,
        )
        get_or_create_course_equivalency(
            db,
            left_course_id=left_course.id,
            right_course_id=right_course.id,
            equivalence_type=equivalence_type,
        )


def seed_official_curricula_with_commit(db: Session) -> None:
    seed_official_curricula(db)
    db.commit()


def main() -> None:
    db = SessionLocal()
    try:
        seed_official_curricula_with_commit(db)
        print("Official curricula seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
