import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import models
from app.modules.registration.errors import (
    AcademicYearNotAllowedError,
    CreditLimitExceededError,
    DepartmentNotAllowedError,
    DuplicateRegistrationError,
    GpaBelowMinimumError,
    IdempotencyConflictError,
    MajorNotAllowedError,
    MissingPrerequisiteError,
    NotFoundError,
    ProfileIncompleteError,
    RegistrationError,
    RegistrationPeriodClosedError,
    TimetableConflictError,
)
from app.modules.registration.publishers import (
    AvailabilityPublisher,
    NoopAvailabilityPublisher,
    NoopRegistrationEventPublisher,
    RegistrationEventPublisher,
)
from app.modules.registration.repository import RegistrationRepository
from app.modules.registration.schemas import (
    EligibilityCheck,
    EligibilityResponse,
    EnrolledResponse,
    RegistrationCreate,
    RegistrationListItem,
    TimetableItem,
    WaitlistedResponse,
)

CREDIT_LIMIT = 18


class RegistrationService:
    def __init__(
        self,
        db: Session,
        availability_publisher: AvailabilityPublisher | None = None,
        event_publisher: RegistrationEventPublisher | None = None,
    ) -> None:
        self.db = db
        self.repo = RegistrationRepository(db)
        self.availability_publisher = availability_publisher or NoopAvailabilityPublisher()
        self.event_publisher = event_publisher or NoopRegistrationEventPublisher()

    def preview_eligibility(self, student_id: int, section_id: int) -> EligibilityResponse:
        context = self._load_context(student_id, section_id, lock_section=False)
        checks = self._build_eligibility_checks(*context)
        student = context[0]
        has_gpa_rule = any(check.rule == "gpa" and check.status != "skipped" for check in checks)
        return EligibilityResponse(
            section_id=section_id,
            eligible=all(check.status != "failed" for check in checks),
            profile_source=student.profile_source,
            gpa_rules_enabled=student.profile_source == "ins_verified" and has_gpa_rule,
            checks=checks,
        )

    def register(self, student_id: int, payload: RegistrationCreate) -> dict[str, Any]:
        request_hash = self._request_hash(payload)
        existing = self.repo.get_idempotency_record(student_id, payload.idempotency_key)
        if existing is not None:
            if existing.request_hash != request_hash:
                raise IdempotencyConflictError()
            return existing.response_body

        event_type = "RegistrationFailed"
        response_body: dict[str, Any] | None = None
        try:
            student, section, offering, course, semester = self._load_context(
                student_id,
                payload.section_id,
                lock_section=True,
            )
            checks = self._build_eligibility_checks(student, section, offering, course, semester)
            self._raise_first_failed_check(checks)
            self._ensure_not_duplicate(student.id, section.id, course.id, semester.id)

            enrolled_count = self.repo.count_active_enrollments(section.id)
            if enrolled_count >= section.capacity:
                waitlist_entry = self.repo.create_waitlist_entry(
                    student_id=student.id,
                    section_id=section.id,
                )
                decision = WaitlistedResponse(
                    waitlist_entry_id=waitlist_entry.id,
                    position=waitlist_entry.position,
                )
                event_type = "StudentWaitlisted"
                entity_id = waitlist_entry.id
            else:
                enrollment = self.repo.create_enrollment(
                    student_id=student.id,
                    section_id=section.id,
                    course_id=course.id,
                    semester_id=semester.id,
                    idempotency_key=payload.idempotency_key,
                )
                remaining_seats = section.capacity - self.repo.count_active_enrollments(section.id)
                decision = EnrolledResponse(
                    enrollment_id=enrollment.id,
                    section_id=section.id,
                    remaining_seats=remaining_seats,
                )
                event_type = "StudentRegistered"
                entity_id = enrollment.id

            response_body = decision.model_dump()
            self.repo.save_idempotency_record(
                student_id=student.id,
                idempotency_key=payload.idempotency_key,
                request_hash=request_hash,
                response_body=response_body,
            )
            self._record_success(student.id, section.id, event_type, entity_id, response_body)
            self.db.commit()
        except RegistrationError as exc:
            self.db.rollback()
            self._record_failure_after_rollback(student_id, payload.section_id, exc)
            raise
        except IntegrityError as exc:
            self.db.rollback()
            duplicate = DuplicateRegistrationError()
            self._record_failure_after_rollback(student_id, payload.section_id, duplicate)
            raise duplicate from exc

        self.availability_publisher.publish_section_changed(payload.section_id)
        self.event_publisher.publish_registration_event(event_type, response_body)
        return response_body

    def drop(self, student_id: int, enrollment_id: int) -> dict[str, str | int]:
        enrollment = self.repo.get_enrollment_for_update(enrollment_id)
        if enrollment is None or enrollment.student_id != student_id:
            raise NotFoundError("Enrollment was not found for this student.")
        if enrollment.status != "enrolled":
            raise DuplicateRegistrationError("Enrollment is not active.")

        enrollment.status = "dropped"
        enrollment.dropped_at = datetime.now(UTC)
        payload = {
            "status": "dropped",
            "enrollment_id": enrollment.id,
            "section_id": enrollment.section_id,
        }
        self.repo.add_audit_log(
            student_id=student_id,
            event_type="student_dropped",
            entity_type="enrollment",
            entity_id=enrollment.id,
            payload=payload,
        )
        self.repo.add_registration_event(
            student_id=student_id,
            section_id=enrollment.section_id,
            event_type="StudentDropped",
            payload=payload,
        )
        self.db.commit()
        self.availability_publisher.publish_section_changed(enrollment.section_id)
        self.event_publisher.publish_registration_event("StudentDropped", payload)
        return payload

    def list_current(self, student_id: int) -> list[RegistrationListItem]:
        items: list[RegistrationListItem] = []
        for enrollment in self.repo.active_enrollments_for_student(student_id):
            section = self.repo.get_section(enrollment.section_id)
            course = self.repo.get_course(enrollment.course_id)
            semester = self.repo.get_semester(enrollment.semester_id)
            if section is None or course is None or semester is None:
                continue
            items.append(
                RegistrationListItem(
                    enrollment_id=enrollment.id,
                    section_id=section.id,
                    course_id=course.id,
                    course_code=course.code,
                    course_title=course.title,
                    semester_id=semester.id,
                    semester_name=semester.name,
                    status=enrollment.status,
                )
            )
        return items

    def timetable(self, student_id: int) -> list[TimetableItem]:
        items: list[TimetableItem] = []
        for enrollment in self.repo.active_enrollments_for_student(student_id):
            course = self.repo.get_course(enrollment.course_id)
            if course is None:
                continue
            for schedule in self.repo.get_section_schedules(enrollment.section_id):
                items.append(
                    TimetableItem(
                        enrollment_id=enrollment.id,
                        section_id=enrollment.section_id,
                        course_code=course.code,
                        course_title=course.title,
                        day_of_week=schedule.day_of_week,
                        start_time=schedule.start_time,
                        end_time=schedule.end_time,
                    )
                )
        return items

    def _load_context(
        self,
        student_id: int,
        section_id: int,
        *,
        lock_section: bool,
    ) -> tuple[
        models.Student,
        models.Section,
        models.CourseOffering,
        models.Course,
        models.Semester,
    ]:
        student = self.repo.get_student(student_id)
        section = (
            self.repo.get_section_for_update(section_id)
            if lock_section
            else self.repo.get_section(section_id)
        )
        if student is None:
            raise NotFoundError("Student was not found.")
        if section is None:
            raise NotFoundError("Section was not found.")

        offering = self.repo.get_offering(section.course_offering_id)
        if offering is None:
            raise NotFoundError("Course offering was not found.")
        course = self.repo.get_course(offering.course_id)
        semester = self.repo.get_semester(offering.semester_id)
        if course is None:
            raise NotFoundError("Course was not found.")
        if semester is None:
            raise NotFoundError("Semester was not found.")
        return student, section, offering, course, semester

    def _build_eligibility_checks(
        self,
        student: models.Student,
        section: models.Section,
        offering: models.CourseOffering,
        course: models.Course,
        semester: models.Semester,
    ) -> list[EligibilityCheck]:
        profile = student.academic_profile
        checks = [
            self._profile_check(student),
            self._registration_period_check(semester.id),
            self._duplicate_check(student.id, section.id, course.id, semester.id),
            self._prerequisite_check(student.id, course.id),
            *self._course_rule_checks(student, course.id),
            self._timetable_check(student.id, section.id),
            self._credit_limit_check(student.id, semester.id, course.credits),
        ]
        if profile is not None and student.profile_source == "manual":
            checks.append(
                EligibilityCheck(
                    rule="profile_source",
                    status="passed",
                    message="Manual academic profile is used for non-GPA eligibility rules.",
                )
            )
        return checks

    def _profile_check(self, student: models.Student) -> EligibilityCheck:
        profile = student.academic_profile
        complete = (
            profile is not None
            and profile.department_id is not None
            and profile.major_id is not None
            and profile.academic_year is not None
        )
        return EligibilityCheck(
            rule="profile",
            status="passed" if complete else "failed",
            message=(
                "Academic profile is complete."
                if complete
                else "Academic profile must include department, major, and academic year."
            ),
        )

    def _registration_period_check(self, semester_id: int) -> EligibilityCheck:
        is_open = any(
            self._is_period_open(period)
            for period in self.repo.get_registration_periods(semester_id)
        )
        return EligibilityCheck(
            rule="registration_period",
            status="passed" if is_open else "failed",
            message=(
                "Registration period is open."
                if is_open
                else "Registration is not open for this semester."
            ),
        )

    def _duplicate_check(
        self,
        student_id: int,
        section_id: int,
        course_id: int,
        semester_id: int,
    ) -> EligibilityCheck:
        duplicate = (
            self.repo.get_active_section_enrollment(student_id, section_id) is not None
            or self.repo.get_active_course_enrollment(student_id, course_id, semester_id)
            is not None
            or self.repo.get_waitlist_entry(student_id, section_id) is not None
        )
        return EligibilityCheck(
            rule="duplicate_registration",
            status="failed" if duplicate else "passed",
            message=(
                "Student already has an active registration or waitlist entry."
                if duplicate
                else "No duplicate registration exists."
            ),
        )

    def _prerequisite_check(self, student_id: int, course_id: int) -> EligibilityCheck:
        completed_codes = self.repo.get_completed_course_codes(student_id)
        missing = [
            course.code
            for course in self.repo.get_prerequisites(course_id)
            if course.code not in completed_codes
        ]
        return EligibilityCheck(
            rule="prerequisite",
            status="failed" if missing else "passed",
            message=(
                f"Missing prerequisite: {missing[0]}."
                if missing
                else "Required courses are completed."
            ),
        )

    def _course_rule_checks(
        self, student: models.Student, course_id: int
    ) -> list[EligibilityCheck]:
        profile = student.academic_profile
        checks: list[EligibilityCheck] = []
        for rule in self.repo.get_course_rules(course_id):
            if rule.min_academic_year is not None:
                passed = profile is not None and profile.academic_year >= rule.min_academic_year
                checks.append(
                    EligibilityCheck(
                        rule="academic_year",
                        status="passed" if passed else "failed",
                        message=(
                            "Academic year requirement is satisfied."
                            if passed
                            else f"Requires academic year {rule.min_academic_year} or higher."
                        ),
                    )
                )
            if rule.allowed_department_ids:
                passed = (
                    profile is not None and profile.department_id in rule.allowed_department_ids
                )
                checks.append(
                    EligibilityCheck(
                        rule="department",
                        status="passed" if passed else "failed",
                        message=(
                            "Department requirement is satisfied."
                            if passed
                            else "Your department is not allowed for this course."
                        ),
                    )
                )
            if rule.allowed_major_ids:
                passed = profile is not None and profile.major_id in rule.allowed_major_ids
                checks.append(
                    EligibilityCheck(
                        rule="major",
                        status="passed" if passed else "failed",
                        message=(
                            "Major requirement is satisfied."
                            if passed
                            else "Your major is not allowed for this course."
                        ),
                    )
                )
            if rule.min_gpa is not None:
                checks.append(self._gpa_check(student, float(rule.min_gpa)))
        return checks

    def _gpa_check(self, student: models.Student, min_gpa: float) -> EligibilityCheck:
        profile = student.academic_profile
        if student.profile_source == "manual":
            message = "GPA is skipped because the student profile is manual and not INS-verified."
            return EligibilityCheck(
                rule="gpa",
                status="skipped",
                message=message,
            )
        passed = (
            profile is not None
            and profile.gpa_is_verified
            and profile.current_gpa is not None
            and float(profile.current_gpa) >= min_gpa
        )
        return EligibilityCheck(
            rule="gpa",
            status="passed" if passed else "failed",
            message=(
                "Verified GPA requirement is satisfied."
                if passed
                else f"Requires verified GPA of at least {min_gpa:.2f}."
            ),
        )

    def _timetable_check(self, student_id: int, section_id: int) -> EligibilityCheck:
        conflict = self.repo.has_timetable_conflict(student_id, section_id)
        return EligibilityCheck(
            rule="timetable",
            status="failed" if conflict else "passed",
            message="Timetable conflict detected." if conflict else "No timetable conflict found.",
        )

    def _credit_limit_check(
        self,
        student_id: int,
        semester_id: int,
        target_credits: int,
    ) -> EligibilityCheck:
        total = self.repo.active_credit_total(student_id, semester_id) + target_credits
        return EligibilityCheck(
            rule="credit_limit",
            status="passed" if total <= CREDIT_LIMIT else "failed",
            message=(
                f"Credit total after registration is {total}/{CREDIT_LIMIT}."
                if total <= CREDIT_LIMIT
                else f"Credit total would be {total}/{CREDIT_LIMIT}."
            ),
        )

    def _raise_first_failed_check(self, checks: list[EligibilityCheck]) -> None:
        for check in checks:
            if check.status != "failed":
                continue
            if check.rule == "profile":
                raise ProfileIncompleteError()
            if check.rule == "registration_period":
                raise RegistrationPeriodClosedError()
            if check.rule == "duplicate_registration":
                raise DuplicateRegistrationError()
            if check.rule == "prerequisite":
                missing_code = check.message.removeprefix("Missing prerequisite: ").removesuffix(
                    "."
                )
                raise MissingPrerequisiteError(missing_code)
            if check.rule == "academic_year":
                raise AcademicYearNotAllowedError()
            if check.rule == "department":
                raise DepartmentNotAllowedError()
            if check.rule == "major":
                raise MajorNotAllowedError()
            if check.rule == "gpa":
                min_gpa = self._parse_min_gpa(check.message)
                raise GpaBelowMinimumError(min_gpa)
            if check.rule == "timetable":
                raise TimetableConflictError()
            if check.rule == "credit_limit":
                raise CreditLimitExceededError()

    def _ensure_not_duplicate(
        self,
        student_id: int,
        section_id: int,
        course_id: int,
        semester_id: int,
    ) -> None:
        duplicate = self._duplicate_check(student_id, section_id, course_id, semester_id)
        if duplicate.status == "failed":
            raise DuplicateRegistrationError()

    def _record_success(
        self,
        student_id: int,
        section_id: int,
        event_type: str,
        entity_id: int,
        payload: dict[str, Any],
    ) -> None:
        audit_event = (
            "student_registered" if event_type == "StudentRegistered" else "student_waitlisted"
        )
        self.repo.add_audit_log(
            student_id=student_id,
            event_type=audit_event,
            entity_type="registration",
            entity_id=entity_id,
            payload=payload,
        )
        self.repo.add_registration_event(
            student_id=student_id,
            section_id=section_id,
            event_type=event_type,
            payload=payload,
        )

    def _record_failure_after_rollback(
        self,
        student_id: int,
        section_id: int,
        exc: RegistrationError,
    ) -> None:
        self.repo.add_audit_log(
            student_id=student_id,
            event_type="registration_failed",
            entity_type="section",
            entity_id=section_id,
            payload={"error": exc.code, "message": exc.message},
        )
        self.repo.add_registration_event(
            student_id=student_id,
            section_id=section_id,
            event_type="RegistrationFailed",
            payload={"error": exc.code, "message": exc.message},
        )
        self.db.commit()

    @staticmethod
    def _is_period_open(period: models.RegistrationPeriod) -> bool:
        now = datetime.utcnow()
        opens_at = RegistrationService._to_utc_naive(period.opens_at)
        closes_at = RegistrationService._to_utc_naive(period.closes_at)
        return opens_at <= now <= closes_at

    @staticmethod
    def _to_utc_naive(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value
        return value.astimezone(UTC).replace(tzinfo=None)

    @staticmethod
    def _request_hash(payload: RegistrationCreate) -> str:
        raw = json.dumps(payload.model_dump(), sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _parse_min_gpa(message: str) -> float:
        try:
            return float(message.rsplit(" ", 1)[-1].removesuffix("."))
        except ValueError:
            return 0.0
