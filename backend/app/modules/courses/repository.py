from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import models


class CourseCatalogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_departments(self) -> list[models.Department]:
        stmt = select(models.Department).order_by(models.Department.code)
        return list(self.db.execute(stmt).scalars())

    def get_department(self, department_id: int) -> models.Department | None:
        return self.db.get(models.Department, department_id)

    def department_code_exists(self, code: str) -> bool:
        stmt = select(models.Department.id).where(
            func.lower(models.Department.code) == code.lower()
        )
        return self.db.execute(stmt).first() is not None

    def department_name_exists(self, name: str) -> bool:
        stmt = select(models.Department.id).where(
            func.lower(models.Department.name) == name.lower()
        )
        return self.db.execute(stmt).first() is not None

    def create_department(self, *, code: str, name: str) -> models.Department:
        department = models.Department(code=code, name=name)
        self.db.add(department)
        self.db.flush()
        return department

    def list_majors(self, *, department_id: int | None = None) -> list[models.Major]:
        stmt = select(models.Major).order_by(models.Major.code)
        if department_id is not None:
            stmt = stmt.where(models.Major.department_id == department_id)
        return list(self.db.execute(stmt).scalars())

    def get_major(self, major_id: int) -> models.Major | None:
        return self.db.get(models.Major, major_id)

    def major_exists_in_department(self, *, department_id: int, code: str, name: str) -> bool:
        stmt = select(models.Major.id).where(
            models.Major.department_id == department_id,
            or_(
                func.lower(models.Major.code) == code.lower(),
                func.lower(models.Major.name) == name.lower(),
            ),
        )
        return self.db.execute(stmt).first() is not None

    def create_major(self, *, department_id: int, code: str, name: str) -> models.Major:
        major = models.Major(department_id=department_id, code=code, name=name)
        self.db.add(major)
        self.db.flush()
        return major

    def list_semesters(self) -> list[models.Semester]:
        stmt = select(models.Semester).order_by(models.Semester.name.desc())
        return list(self.db.execute(stmt).scalars())

    def get_semester(self, semester_id: int) -> models.Semester | None:
        return self.db.get(models.Semester, semester_id)

    def semester_name_exists(self, name: str) -> bool:
        stmt = select(models.Semester.id).where(func.lower(models.Semester.name) == name.lower())
        return self.db.execute(stmt).first() is not None

    def create_semester(self, *, name: str, status: str) -> models.Semester:
        semester = models.Semester(name=name, status=status)
        self.db.add(semester)
        self.db.flush()
        return semester

    def list_courses(self) -> list[models.Course]:
        stmt = select(models.Course).order_by(models.Course.code)
        return list(self.db.execute(stmt).scalars())

    def get_course(self, course_id: int) -> models.Course | None:
        return self.db.get(models.Course, course_id)

    def get_course_by_identity(
        self,
        *,
        code: str,
        title: str,
        credits: int,
    ) -> models.Course | None:
        stmt = select(models.Course).where(
            func.lower(models.Course.code) == code.lower(),
            func.lower(models.Course.title) == title.lower(),
            models.Course.credits == credits,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_courses_by_code(self, code: str) -> list[models.Course]:
        stmt = select(models.Course).where(func.lower(models.Course.code) == code.lower())
        return list(self.db.execute(stmt).scalars())

    def create_course(self, **kwargs: object) -> models.Course:
        course = models.Course(**kwargs)
        self.db.add(course)
        self.db.flush()
        return course

    def list_prerequisite_rows(self, course_id: int) -> list[models.CoursePrerequisite]:
        stmt = (
            select(models.CoursePrerequisite)
            .where(models.CoursePrerequisite.course_id == course_id)
            .order_by(models.CoursePrerequisite.prerequisite_course_id)
        )
        return list(self.db.execute(stmt).scalars())

    def get_course_rules(self, course_id: int) -> list[models.CourseEligibilityRule]:
        stmt = select(models.CourseEligibilityRule).where(
            models.CourseEligibilityRule.course_id == course_id
        )
        return list(self.db.execute(stmt).scalars())

    def create_course_rule(
        self, *, course_id: int, **kwargs: object
    ) -> models.CourseEligibilityRule:
        rule = models.CourseEligibilityRule(course_id=course_id, **kwargs)
        self.db.add(rule)
        self.db.flush()
        return rule

    def delete_prerequisites(self, course_id: int) -> None:
        stmt = select(models.CoursePrerequisite).where(
            models.CoursePrerequisite.course_id == course_id
        )
        for row in self.db.execute(stmt).scalars():
            self.db.delete(row)
        self.db.flush()

    def add_prerequisites(
        self,
        *,
        course_id: int,
        prerequisite_course_ids: Sequence[int],
        rule_group: str,
    ) -> list[models.CoursePrerequisite]:
        rows: list[models.CoursePrerequisite] = []
        for prerequisite_course_id in prerequisite_course_ids:
            row = models.CoursePrerequisite(
                course_id=course_id,
                prerequisite_course_id=prerequisite_course_id,
                rule_group=rule_group,
            )
            self.db.add(row)
            rows.append(row)
        self.db.flush()
        return rows

    def prerequisite_ids_for_course(self, course_id: int) -> list[int]:
        stmt = select(models.CoursePrerequisite.prerequisite_course_id).where(
            models.CoursePrerequisite.course_id == course_id
        )
        return list(self.db.execute(stmt).scalars())

    def get_course_offering(self, offering_id: int) -> models.CourseOffering | None:
        return self.db.get(models.CourseOffering, offering_id)

    def get_course_offering_by_course_and_semester(
        self,
        *,
        course_id: int,
        semester_id: int,
    ) -> models.CourseOffering | None:
        stmt = select(models.CourseOffering).where(
            models.CourseOffering.course_id == course_id,
            models.CourseOffering.semester_id == semester_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_course_offerings(
        self, *, semester_id: int | None = None
    ) -> list[models.CourseOffering]:
        stmt = select(models.CourseOffering).order_by(models.CourseOffering.created_at.desc())
        if semester_id is not None:
            stmt = stmt.where(models.CourseOffering.semester_id == semester_id)
        return list(self.db.execute(stmt).scalars())

    def create_course_offering(
        self,
        *,
        course_id: int,
        semester_id: int,
        status: str,
    ) -> models.CourseOffering:
        offering = models.CourseOffering(
            course_id=course_id, semester_id=semester_id, status=status
        )
        self.db.add(offering)
        self.db.flush()
        return offering

    def get_professor(self, professor_id: int) -> models.Professor | None:
        return self.db.get(models.Professor, professor_id)

    def get_section(self, section_id: int) -> models.Section | None:
        return self.db.get(models.Section, section_id)

    def get_section_by_code(
        self,
        *,
        course_offering_id: int,
        section_code: str,
    ) -> models.Section | None:
        stmt = select(models.Section).where(
            models.Section.course_offering_id == course_offering_id,
            func.lower(models.Section.section_code) == section_code.lower(),
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_sections(
        self,
        *,
        course_id: int | None = None,
        semester_id: int | None = None,
    ) -> list[models.Section]:
        stmt = (
            select(models.Section)
            .join(
                models.CourseOffering, models.CourseOffering.id == models.Section.course_offering_id
            )
            .order_by(models.Section.section_code)
        )
        if course_id is not None:
            stmt = stmt.where(models.CourseOffering.course_id == course_id)
        if semester_id is not None:
            stmt = stmt.where(models.CourseOffering.semester_id == semester_id)
        return list(self.db.execute(stmt).scalars())

    def create_section(self, **kwargs: object) -> models.Section:
        section = models.Section(**kwargs)
        self.db.add(section)
        self.db.flush()
        return section

    def list_registration_periods(
        self,
        *,
        semester_id: int | None = None,
    ) -> list[models.RegistrationPeriod]:
        stmt = select(models.RegistrationPeriod).order_by(models.RegistrationPeriod.opens_at.desc())
        if semester_id is not None:
            stmt = stmt.where(models.RegistrationPeriod.semester_id == semester_id)
        return list(self.db.execute(stmt).scalars())

    def create_registration_period(
        self,
        *,
        semester_id: int,
        opens_at,
        closes_at,
        status: str,
    ) -> models.RegistrationPeriod:
        period = models.RegistrationPeriod(
            semester_id=semester_id,
            opens_at=opens_at,
            closes_at=closes_at,
            status=status,
        )
        self.db.add(period)
        self.db.flush()
        return period

    def overlapping_period_exists(self, *, semester_id: int, opens_at, closes_at) -> bool:
        stmt = select(models.RegistrationPeriod.id).where(
            models.RegistrationPeriod.semester_id == semester_id,
            models.RegistrationPeriod.opens_at < closes_at,
            models.RegistrationPeriod.closes_at > opens_at,
        )
        return self.db.execute(stmt).first() is not None

    def count_sections_for_offering(self, offering_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(models.Section)
            .where(models.Section.course_offering_id == offering_id)
        )
        return int(self.db.execute(stmt).scalar_one())

    def count_active_enrollments(self, section_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(models.Enrollment)
            .where(
                models.Enrollment.section_id == section_id,
                models.Enrollment.status == "enrolled",
            )
        )
        return int(self.db.execute(stmt).scalar_one())

    def count_waitlist_entries(self, section_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(models.WaitlistEntry)
            .where(
                models.WaitlistEntry.section_id == section_id,
                models.WaitlistEntry.status == "waiting",
            )
        )
        return int(self.db.execute(stmt).scalar_one())

    def create_audit_log(
        self,
        *,
        actor_student_id: int | None,
        event_type: str,
        entity_type: str,
        entity_id: int | None,
        payload: dict | None,
    ) -> None:
        self.db.add(
            models.AuditLog(
                actor_student_id=actor_student_id,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                payload=payload,
            )
        )
