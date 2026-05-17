from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.db import models


class RegistrationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_student(self, student_id: int) -> models.Student | None:
        return self.db.get(models.Student, student_id)

    def get_section_for_update(self, section_id: int) -> models.Section | None:
        stmt = select(models.Section).where(models.Section.id == section_id).with_for_update()
        return self.db.execute(stmt).scalar_one_or_none()

    def get_section(self, section_id: int) -> models.Section | None:
        return self.db.get(models.Section, section_id)

    def get_offering(self, offering_id: int) -> models.CourseOffering | None:
        return self.db.get(models.CourseOffering, offering_id)

    def get_course(self, course_id: int) -> models.Course | None:
        return self.db.get(models.Course, course_id)

    def get_semester(self, semester_id: int) -> models.Semester | None:
        return self.db.get(models.Semester, semester_id)

    def get_registration_periods(self, semester_id: int) -> list[models.RegistrationPeriod]:
        stmt = select(models.RegistrationPeriod).where(
            models.RegistrationPeriod.semester_id == semester_id,
            models.RegistrationPeriod.status == "open",
        )
        return list(self.db.execute(stmt).scalars())

    def get_course_rules(self, course_id: int) -> list[models.CourseEligibilityRule]:
        stmt = select(models.CourseEligibilityRule).where(
            models.CourseEligibilityRule.course_id == course_id,
        )
        return list(self.db.execute(stmt).scalars())

    def get_prerequisites(self, course_id: int) -> list[models.Course]:
        stmt = (
            select(models.Course)
            .join(
                models.CoursePrerequisite,
                models.CoursePrerequisite.prerequisite_course_id == models.Course.id,
            )
            .where(models.CoursePrerequisite.course_id == course_id)
        )
        return list(self.db.execute(stmt).scalars())

    def get_completed_course_codes(self, student_id: int) -> set[str]:
        stmt = select(models.StudentCompletedCourse.course_code).where(
            models.StudentCompletedCourse.student_id == student_id,
        )
        return set(self.db.execute(stmt).scalars())

    def get_completed_course_ids(self, student_id: int) -> set[int]:
        stmt = select(models.StudentCompletedCourse.course_id).where(
            models.StudentCompletedCourse.student_id == student_id,
            models.StudentCompletedCourse.course_id.is_not(None),
        )
        return {int(value) for value in self.db.execute(stmt).scalars()}

    def get_active_course_enrollment(
        self,
        student_id: int,
        course_id: int,
        semester_id: int,
    ) -> models.Enrollment | None:
        stmt = select(models.Enrollment).where(
            models.Enrollment.student_id == student_id,
            models.Enrollment.course_id == course_id,
            models.Enrollment.semester_id == semester_id,
            models.Enrollment.status == "enrolled",
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_active_section_enrollment(
        self,
        student_id: int,
        section_id: int,
    ) -> models.Enrollment | None:
        stmt = select(models.Enrollment).where(
            models.Enrollment.student_id == student_id,
            models.Enrollment.section_id == section_id,
            models.Enrollment.status == "enrolled",
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_waitlist_entry(
        self,
        student_id: int,
        section_id: int,
        statuses: tuple[str, ...] = ("waiting",),
    ) -> models.WaitlistEntry | None:
        stmt = select(models.WaitlistEntry).where(
            models.WaitlistEntry.student_id == student_id,
            models.WaitlistEntry.section_id == section_id,
            models.WaitlistEntry.status.in_(statuses),
        )
        return self.db.execute(stmt).scalar_one_or_none()

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

    def next_waitlist_position(self, section_id: int) -> int:
        stmt = select(func.coalesce(func.max(models.WaitlistEntry.position), 0)).where(
            models.WaitlistEntry.section_id == section_id,
        )
        return int(self.db.execute(stmt).scalar_one()) + 1

    def create_enrollment(
        self,
        *,
        student_id: int,
        section_id: int,
        course_id: int,
        semester_id: int,
        idempotency_key: str,
    ) -> models.Enrollment:
        enrollment = models.Enrollment(
            student_id=student_id,
            section_id=section_id,
            course_id=course_id,
            semester_id=semester_id,
            idempotency_key=idempotency_key,
            status="enrolled",
        )
        self.db.add(enrollment)
        self.db.flush()
        return enrollment

    def create_waitlist_entry(self, *, student_id: int, section_id: int) -> models.WaitlistEntry:
        entry = models.WaitlistEntry(
            student_id=student_id,
            section_id=section_id,
            position=self.next_waitlist_position(section_id),
            status="waiting",
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def get_enrollment_for_update(self, enrollment_id: int) -> models.Enrollment | None:
        stmt = (
            select(models.Enrollment).where(models.Enrollment.id == enrollment_id).with_for_update()
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def active_enrollments_for_student(self, student_id: int) -> list[models.Enrollment]:
        stmt = (
            select(models.Enrollment)
            .where(
                models.Enrollment.student_id == student_id,
                models.Enrollment.status == "enrolled",
            )
            .order_by(models.Enrollment.enrolled_at.desc())
        )
        return list(self.db.execute(stmt).scalars())

    def get_section_schedules(self, section_id: int) -> list[models.SectionSchedule]:
        stmt = select(models.SectionSchedule).where(models.SectionSchedule.section_id == section_id)
        return list(self.db.execute(stmt).scalars())

    def has_timetable_conflict(self, student_id: int, target_section_id: int) -> bool:
        target_schedules = self.get_section_schedules(target_section_id)
        if not target_schedules:
            return False

        enrolled_section_ids = select(models.Enrollment.section_id).where(
            models.Enrollment.student_id == student_id,
            models.Enrollment.status == "enrolled",
        )
        for schedule in target_schedules:
            stmt = select(models.SectionSchedule.id).where(
                models.SectionSchedule.section_id.in_(enrolled_section_ids),
                models.SectionSchedule.day_of_week == schedule.day_of_week,
                or_(
                    and_(
                        models.SectionSchedule.start_time < schedule.end_time,
                        models.SectionSchedule.end_time > schedule.start_time,
                    ),
                ),
            )
            if self.db.execute(stmt).first() is not None:
                return True
        return False

    def active_credit_total(self, student_id: int, semester_id: int) -> int:
        stmt = (
            select(func.coalesce(func.sum(models.Course.credits), 0))
            .select_from(models.Enrollment)
            .join(models.Course, models.Course.id == models.Enrollment.course_id)
            .where(
                models.Enrollment.student_id == student_id,
                models.Enrollment.semester_id == semester_id,
                models.Enrollment.status == "enrolled",
            )
        )
        return int(self.db.execute(stmt).scalar_one())

    def get_idempotency_record(
        self,
        student_id: int,
        idempotency_key: str,
    ) -> models.RegistrationIdempotencyKey | None:
        stmt = select(models.RegistrationIdempotencyKey).where(
            models.RegistrationIdempotencyKey.student_id == student_id,
            models.RegistrationIdempotencyKey.idempotency_key == idempotency_key,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def save_idempotency_record(
        self,
        *,
        student_id: int,
        idempotency_key: str,
        request_hash: str,
        response_body: dict,
        status_code: int = 200,
    ) -> None:
        self.db.add(
            models.RegistrationIdempotencyKey(
                student_id=student_id,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_body=response_body,
                status_code=status_code,
            )
        )

    def add_audit_log(
        self,
        *,
        student_id: int | None,
        event_type: str,
        entity_type: str,
        entity_id: int | None,
        payload: dict | None = None,
    ) -> None:
        self.db.add(
            models.AuditLog(
                actor_student_id=student_id,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                payload=payload,
            )
        )

    def add_registration_event(
        self,
        *,
        student_id: int | None,
        section_id: int | None,
        event_type: str,
        payload: dict | None = None,
    ) -> models.RegistrationEvent:
        event = models.RegistrationEvent(
            student_id=student_id,
            section_id=section_id,
            event_type=event_type,
            payload=payload,
        )
        self.db.add(event)
        self.db.flush()
        return event
