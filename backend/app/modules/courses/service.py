from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db import models
from app.modules.courses import schemas
from app.modules.courses.repository import CourseCatalogRepository
from app.modules.registration.service import RegistrationService


class CourseCatalogService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CourseCatalogRepository(db)

    def list_departments(self) -> list[schemas.DepartmentRead]:
        return [
            schemas.DepartmentRead(id=department.id, code=department.code, name=department.name)
            for department in self.repo.list_departments()
        ]

    def create_department(self, payload: schemas.DepartmentCreate) -> schemas.DepartmentRead:
        if self.repo.department_code_exists(payload.code):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Department code already exists."
            )
        if self.repo.department_name_exists(payload.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Department name already exists."
            )
        department = self.repo.create_department(code=payload.code, name=payload.name)
        self.db.commit()
        return schemas.DepartmentRead(id=department.id, code=department.code, name=department.name)

    def list_majors(self, *, department_id: int | None = None) -> list[schemas.MajorRead]:
        return [
            schemas.MajorRead(
                id=major.id,
                department_id=major.department_id,
                code=major.code,
                name=major.name,
            )
            for major in self.repo.list_majors(department_id=department_id)
        ]

    def create_major(self, payload: schemas.MajorCreate) -> schemas.MajorRead:
        if self.repo.get_department(payload.department_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Department not found."
            )
        if self.repo.major_exists_in_department(
            department_id=payload.department_id,
            code=payload.code,
            name=payload.name,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A major with this code or name already exists in the department.",
            )
        major = self.repo.create_major(
            department_id=payload.department_id,
            code=payload.code,
            name=payload.name,
        )
        self.db.commit()
        return schemas.MajorRead(
            id=major.id,
            department_id=major.department_id,
            code=major.code,
            name=major.name,
        )

    def list_semesters(self) -> list[schemas.SemesterRead]:
        return [
            schemas.SemesterRead(id=semester.id, name=semester.name, status=semester.status)
            for semester in self.repo.list_semesters()
        ]

    def create_semester(self, payload: schemas.SemesterCreate) -> schemas.SemesterRead:
        if self.repo.semester_name_exists(payload.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Semester name already exists."
            )
        semester = self.repo.create_semester(name=payload.name, status=payload.status)
        self.db.commit()
        return schemas.SemesterRead(id=semester.id, name=semester.name, status=semester.status)

    def list_admin_courses(self) -> list[schemas.CourseSummary]:
        return [self._build_course_summary(course) for course in self.repo.list_courses()]

    def create_course(self, payload: schemas.CourseCreate) -> schemas.CourseDetail:
        if (
            payload.department_id is not None
            and self.repo.get_department(payload.department_id) is None
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Department not found."
            )
        if (
            self.repo.get_course_by_identity(
                code=payload.code,
                title=payload.title,
                credits=payload.credits,
            )
            is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An identical course already exists.",
            )
        course = self.repo.create_course(**payload.model_dump())
        self.db.commit()
        return self.get_course_detail(course.id)

    def get_course_detail(self, course_id: int) -> schemas.CourseDetail:
        course = self.repo.get_course(course_id)
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")
        department = (
            self.repo.get_department(course.department_id) if course.department_id else None
        )
        prerequisites = []
        for row in self.repo.list_prerequisite_rows(course.id):
            prerequisite = self.repo.get_course(row.prerequisite_course_id)
            if prerequisite is None:
                continue
            prerequisites.append(
                schemas.CourseReference(
                    id=prerequisite.id,
                    code=prerequisite.code,
                    title=prerequisite.title,
                )
            )
        return schemas.CourseDetail(
            id=course.id,
            department_id=course.department_id,
            department_code=department.code if department else None,
            department_name=department.name if department else None,
            code=course.code,
            title=course.title,
            credits=course.credits,
            description=course.description,
            course_type=course.course_type,
            is_repeatable=course.is_repeatable,
            prerequisites=prerequisites,
        )

    def replace_prerequisites(
        self,
        course_id: int,
        payload: schemas.PrerequisiteReplaceRequest,
    ) -> list[schemas.CoursePrerequisiteRead]:
        course = self.repo.get_course(course_id)
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

        prerequisite_courses: list[models.Course] = []
        for prerequisite_course_id in payload.prerequisite_course_ids:
            if prerequisite_course_id == course_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A course cannot require itself as a prerequisite.",
                )
            prerequisite_course = self.repo.get_course(prerequisite_course_id)
            if prerequisite_course is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Prerequisite course {prerequisite_course_id} was not found.",
                )
            if self._would_create_cycle(course_id, prerequisite_course_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Adding {prerequisite_course.code} would create a prerequisite cycle."
                    ),
                )
            prerequisite_courses.append(prerequisite_course)

        self.repo.delete_prerequisites(course_id)
        self.repo.add_prerequisites(
            course_id=course_id,
            prerequisite_course_ids=payload.prerequisite_course_ids,
            rule_group=payload.rule_group,
        )
        self.repo.create_audit_log(
            actor_student_id=None,
            event_type="admin_prerequisites_replaced",
            entity_type="course",
            entity_id=course_id,
            payload={"prerequisite_course_ids": payload.prerequisite_course_ids},
        )
        self.db.commit()
        return [
            schemas.CoursePrerequisiteRead(
                prerequisite_course_id=prerequisite.id,
                prerequisite_code=prerequisite.code,
                prerequisite_title=prerequisite.title,
                rule_group=payload.rule_group,
            )
            for prerequisite in prerequisite_courses
        ]

    def list_course_offerings(
        self, *, semester_id: int | None = None
    ) -> list[schemas.CourseOfferingRead]:
        return [
            self._build_course_offering_read(offering)
            for offering in self.repo.list_course_offerings(semester_id=semester_id)
        ]

    def create_course_offering(
        self,
        payload: schemas.CourseOfferingCreate,
    ) -> schemas.CourseOfferingRead:
        course = self.repo.get_course(payload.course_id)
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")
        semester = self.repo.get_semester(payload.semester_id)
        if semester is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semester not found.")
        existing = self.repo.get_course_offering_by_course_and_semester(
            course_id=payload.course_id,
            semester_id=payload.semester_id,
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This course already has an offering for the selected semester.",
            )
        offering = self.repo.create_course_offering(**payload.model_dump())
        self.repo.create_audit_log(
            actor_student_id=None,
            event_type="admin_course_offering_created",
            entity_type="course_offering",
            entity_id=offering.id,
            payload=payload.model_dump(),
        )
        self.db.commit()
        return self._build_course_offering_read(offering)

    def list_sections(
        self,
        *,
        course_id: int | None = None,
        semester_id: int | None = None,
    ) -> list[schemas.SectionSummary]:
        return [
            self._build_section_summary(section)
            for section in self.repo.list_sections(course_id=course_id, semester_id=semester_id)
        ]

    def create_section(self, payload: schemas.SectionCreate) -> schemas.SectionSummary:
        offering = self.repo.get_course_offering(payload.course_offering_id)
        if offering is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Course offering not found."
            )
        if (
            payload.professor_id is not None
            and self.repo.get_professor(payload.professor_id) is None
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Professor not found."
            )
        if (
            self.repo.get_section_by_code(
                course_offering_id=payload.course_offering_id,
                section_code=payload.section_code,
            )
            is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Section code already exists for this course offering.",
            )
        section = self.repo.create_section(**payload.model_dump())
        self.repo.create_audit_log(
            actor_student_id=None,
            event_type="admin_section_created",
            entity_type="section",
            entity_id=section.id,
            payload=payload.model_dump(),
        )
        self.db.commit()
        return self._build_section_summary(section)

    def create_registration_period(
        self,
        payload: schemas.RegistrationPeriodCreate,
    ) -> schemas.RegistrationPeriodRead:
        semester = self.repo.get_semester(payload.semester_id)
        if semester is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semester not found.")
        if self.repo.overlapping_period_exists(
            semester_id=payload.semester_id,
            opens_at=payload.opens_at,
            closes_at=payload.closes_at,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The semester already has an overlapping registration period.",
            )
        period = self.repo.create_registration_period(**payload.model_dump())
        self.repo.create_audit_log(
            actor_student_id=None,
            event_type="admin_registration_period_created",
            entity_type="registration_period",
            entity_id=period.id,
            payload=payload.model_dump(mode="json"),
        )
        self.db.commit()
        return schemas.RegistrationPeriodRead(
            id=period.id,
            semester_id=period.semester_id,
            semester_name=semester.name,
            opens_at=period.opens_at,
            closes_at=period.closes_at,
            status=period.status,
        )

    def list_registration_periods(
        self,
        *,
        semester_id: int | None = None,
    ) -> list[schemas.RegistrationPeriodRead]:
        periods = []
        for period in self.repo.list_registration_periods(semester_id=semester_id):
            semester = self.repo.get_semester(period.semester_id)
            periods.append(
                schemas.RegistrationPeriodRead(
                    id=period.id,
                    semester_id=period.semester_id,
                    semester_name=semester.name if semester else "Unknown",
                    opens_at=period.opens_at,
                    closes_at=period.closes_at,
                    status=period.status,
                )
            )
        return periods

    def list_public_courses(
        self,
        *,
        semester_id: int | None,
        department_id: int | None,
        major_id: int | None,
        search: str | None,
        eligible_only: bool,
        student_id: int | None,
    ) -> list[schemas.CourseSummary]:
        if eligible_only and student_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="eligible_only requires the X-Student-Id header for now.",
            )

        sections = self.repo.list_sections(semester_id=semester_id)
        candidate_offering_ids = {
            section.course_offering_id for section in sections if section.status != "cancelled"
        }
        course_ids: set[int] = set()
        for offering in self.repo.list_course_offerings(semester_id=semester_id):
            if offering.status != "active" or offering.id not in candidate_offering_ids:
                continue
            course_ids.add(offering.course_id)

        search_term = search.lower().strip() if search else None
        summaries: list[schemas.CourseSummary] = []
        for course_id in sorted(course_ids):
            course = self.repo.get_course(course_id)
            if course is None:
                continue
            if department_id is not None and course.department_id != department_id:
                continue
            if search_term and search_term not in f"{course.code} {course.title}".lower():
                continue
            if major_id is not None and not self._course_matches_major_filter(course.id, major_id):
                continue
            if eligible_only and not self._course_has_eligible_section(
                course_id=course.id,
                semester_id=semester_id,
                student_id=student_id,
            ):
                continue
            summaries.append(self._build_course_summary(course))
        return summaries

    def get_section_summary(self, section_id: int) -> schemas.SectionSummary:
        section = self.repo.get_section(section_id)
        if section is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found.")
        return self._build_section_summary(section)

    def get_section_availability(self, section_id: int) -> schemas.SectionAvailability:
        section = self.repo.get_section(section_id)
        if section is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found.")
        enrolled_count = self.repo.count_active_enrollments(section.id)
        waitlist_count = self.repo.count_waitlist_entries(section.id)
        return schemas.SectionAvailability(
            section_id=section.id,
            capacity=section.capacity,
            enrolled_count=enrolled_count,
            remaining_seats=max(section.capacity - enrolled_count, 0),
            waitlist_count=waitlist_count,
            status=section.status,
        )

    def _build_course_summary(self, course: models.Course) -> schemas.CourseSummary:
        department = (
            self.repo.get_department(course.department_id) if course.department_id else None
        )
        active_offering_count = 0
        active_section_count = 0
        for offering in self.repo.list_course_offerings():
            if offering.course_id != course.id or offering.status != "active":
                continue
            active_offering_count += 1
            for section in self.repo.list_sections():
                if section.course_offering_id == offering.id and section.status != "cancelled":
                    active_section_count += 1
        return schemas.CourseSummary(
            id=course.id,
            department_id=course.department_id,
            department_code=department.code if department else None,
            department_name=department.name if department else None,
            code=course.code,
            title=course.title,
            credits=course.credits,
            course_type=course.course_type,
            active_offering_count=active_offering_count,
            active_section_count=active_section_count,
        )

    def _build_course_offering_read(
        self, offering: models.CourseOffering
    ) -> schemas.CourseOfferingRead:
        course = self.repo.get_course(offering.course_id)
        semester = self.repo.get_semester(offering.semester_id)
        return schemas.CourseOfferingRead(
            id=offering.id,
            course_id=offering.course_id,
            course_code=course.code if course else "UNKNOWN",
            course_title=course.title if course else "Unknown course",
            semester_id=offering.semester_id,
            semester_name=semester.name if semester else "Unknown semester",
            status=offering.status,
            section_count=self.repo.count_sections_for_offering(offering.id),
        )

    def _build_section_summary(self, section: models.Section) -> schemas.SectionSummary:
        offering = self.repo.get_course_offering(section.course_offering_id)
        if offering is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Course offering not found."
            )
        course = self.repo.get_course(offering.course_id)
        semester = self.repo.get_semester(offering.semester_id)
        enrolled_count = self.repo.count_active_enrollments(section.id)
        waitlist_count = self.repo.count_waitlist_entries(section.id)
        return schemas.SectionSummary(
            id=section.id,
            course_offering_id=section.course_offering_id,
            course_id=offering.course_id,
            course_code=course.code if course else "UNKNOWN",
            course_title=course.title if course else "Unknown course",
            semester_id=offering.semester_id,
            semester_name=semester.name if semester else "Unknown semester",
            professor_id=section.professor_id,
            section_code=section.section_code,
            capacity=section.capacity,
            enrolled_count=enrolled_count,
            remaining_seats=max(section.capacity - enrolled_count, 0),
            waitlist_count=waitlist_count,
            room_selection_mode=section.room_selection_mode,
            status=section.status,
        )

    def _would_create_cycle(self, course_id: int, prerequisite_course_id: int) -> bool:
        stack = [prerequisite_course_id]
        visited: set[int] = set()
        while stack:
            current = stack.pop()
            if current == course_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            stack.extend(self.repo.prerequisite_ids_for_course(current))
        return False

    def _course_matches_major_filter(self, course_id: int, major_id: int) -> bool:
        rules = self.repo.get_course_rules(course_id)
        if not rules:
            return True
        for rule in rules:
            if not rule.allowed_major_ids:
                return True
            if major_id in rule.allowed_major_ids:
                return True
        return False

    def _course_has_eligible_section(
        self,
        *,
        course_id: int,
        semester_id: int | None,
        student_id: int | None,
    ) -> bool:
        if student_id is None:
            return False
        for section in self.repo.list_sections(course_id=course_id, semester_id=semester_id):
            if section.status != "open":
                continue
            eligibility = RegistrationService(self.db).preview_eligibility(student_id, section.id)
            if eligibility.eligible:
                return True
        return False
