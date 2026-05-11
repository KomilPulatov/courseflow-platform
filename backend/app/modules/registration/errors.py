from http import HTTPStatus


class RegistrationError(Exception):
    code = "registration_error"
    message = "Registration request failed."
    status_code = HTTPStatus.BAD_REQUEST

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message


class NotFoundError(RegistrationError):
    code = "not_found"
    message = "Requested resource was not found."
    status_code = HTTPStatus.NOT_FOUND


class ProfileIncompleteError(RegistrationError):
    code = "profile_incomplete"
    message = "Complete your academic profile before registering."


class RegistrationPeriodClosedError(RegistrationError):
    code = "registration_period_closed"
    message = "Registration is not open for this semester."


class DuplicateRegistrationError(RegistrationError):
    code = "duplicate_registration"
    message = "Student is already registered or waitlisted for this course section."
    status_code = HTTPStatus.CONFLICT


class SectionHasAvailableSeatsError(RegistrationError):
    code = "section_has_available_seats"
    message = "This section still has available seats. Register instead of joining waitlist."
    status_code = HTTPStatus.CONFLICT


class WaitlistEntryNotActiveError(RegistrationError):
    code = "waitlist_entry_not_active"
    message = "Waitlist entry is not active."
    status_code = HTTPStatus.CONFLICT


class MissingPrerequisiteError(RegistrationError):
    code = "missing_prerequisite"

    def __init__(self, course_code: str) -> None:
        super().__init__(f"You have not completed {course_code}.")


class GpaBelowMinimumError(RegistrationError):
    code = "gpa_below_minimum"

    def __init__(self, min_gpa: float) -> None:
        super().__init__(f"This section requires a verified GPA of at least {min_gpa:.2f}.")


class DepartmentNotAllowedError(RegistrationError):
    code = "department_not_allowed"
    message = "Your department is not eligible for this course."


class MajorNotAllowedError(RegistrationError):
    code = "major_not_allowed"
    message = "Your major is not eligible for this course."


class AcademicYearNotAllowedError(RegistrationError):
    code = "academic_year_not_allowed"
    message = "Your academic year is not eligible for this course."


class TimetableConflictError(RegistrationError):
    code = "timetable_conflict"
    message = "This section conflicts with your current timetable."
    status_code = HTTPStatus.CONFLICT


class CreditLimitExceededError(RegistrationError):
    code = "credit_limit_exceeded"
    message = "Registering for this section would exceed the semester credit limit."


class IdempotencyConflictError(RegistrationError):
    code = "idempotency_conflict"
    message = "The idempotency key was already used with a different request."
    status_code = HTTPStatus.CONFLICT
