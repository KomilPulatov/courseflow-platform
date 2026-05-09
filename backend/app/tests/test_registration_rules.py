from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models import CourseEligibilityRule, RegistrationPeriod, StudentCompletedCourse
from app.modules.registration.errors import GpaBelowMinimumError, MissingPrerequisiteError
from app.modules.registration.schemas import RegistrationCreate
from app.modules.registration.service import RegistrationService
from app.tests.factories import seed_registration_case


def test_verified_gpa_is_enforced(db_session: Session) -> None:
    seed = seed_registration_case(db_session, with_gpa_rule=True)
    student = RegistrationService(db_session).repo.get_student(seed["student_id"])
    student.profile_source = "ins_verified"
    student.academic_profile.current_gpa = 2.5
    student.academic_profile.gpa_is_verified = True
    db_session.commit()

    response = RegistrationService(db_session).preview_eligibility(
        seed["student_id"],
        seed["section_id"],
    )

    assert response.eligible is False
    assert any(check.rule == "gpa" and check.status == "failed" for check in response.checks)


def test_registration_raises_for_verified_gpa_below_minimum(db_session: Session) -> None:
    seed = seed_registration_case(db_session, with_gpa_rule=True)
    student = RegistrationService(db_session).repo.get_student(seed["student_id"])
    student.profile_source = "ins_verified"
    student.academic_profile.current_gpa = 2.5
    student.academic_profile.gpa_is_verified = True
    db_session.commit()

    try:
        RegistrationService(db_session).register(
            seed["student_id"],
            RegistrationCreate(section_id=seed["section_id"], idempotency_key="low-gpa-1"),
        )
    except GpaBelowMinimumError as exc:
        assert exc.code == "gpa_below_minimum"
    else:
        raise AssertionError("Expected GPA failure")


def test_missing_prerequisite_fails_registration(db_session: Session) -> None:
    seed = seed_registration_case(db_session, with_prerequisite=True)
    db_session.query(StudentCompletedCourse).delete()
    db_session.commit()

    try:
        RegistrationService(db_session).register(
            seed["student_id"],
            RegistrationCreate(section_id=seed["section_id"], idempotency_key="missing-prereq"),
        )
    except MissingPrerequisiteError as exc:
        assert exc.code == "missing_prerequisite"
        assert "CSE2010" in exc.message
    else:
        raise AssertionError("Expected prerequisite failure")


def test_closed_registration_period_makes_student_ineligible(db_session: Session) -> None:
    seed = seed_registration_case(db_session)
    now = datetime.now(UTC)
    period = db_session.get(RegistrationPeriod, 1)
    period.opens_at = now - timedelta(days=3)
    period.closes_at = now - timedelta(days=1)
    db_session.commit()

    response = RegistrationService(db_session).preview_eligibility(
        seed["student_id"],
        seed["section_id"],
    )

    assert response.eligible is False
    assert any(
        check.rule == "registration_period" and check.status == "failed"
        for check in response.checks
    )


def test_department_rule_failure_is_explainable(db_session: Session) -> None:
    seed = seed_registration_case(db_session)
    db_session.add(CourseEligibilityRule(course_id=1, allowed_department_ids=[99]))
    db_session.commit()

    response = RegistrationService(db_session).preview_eligibility(
        seed["student_id"],
        seed["section_id"],
    )

    assert response.eligible is False
    assert any(check.rule == "department" and check.status == "failed" for check in response.checks)
