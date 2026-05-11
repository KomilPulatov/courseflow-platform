from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.models import (
    Enrollment,
    RegistrationPeriod,
    Section,
    Student,
    StudentAcademicProfile,
    User,
    WaitlistEntry,
)
from app.tests.factories import seed_registration_case


def add_manual_student(db_session: Session, student_id: int) -> None:
    db_session.add(
        Student(
            id=student_id,
            student_number=f"2311{student_id:03d}",
            full_name=f"Student {student_id}",
            profile_source="manual",
        )
    )
    db_session.add(
        StudentAcademicProfile(
            student_id=student_id,
            department_id=1,
            major_id=1,
            academic_year=3,
            gpa_is_verified=False,
        )
    )


def close_registration_period(db_session: Session) -> None:
    now = datetime.now(UTC)
    period = db_session.get(RegistrationPeriod, 1)
    period.opens_at = now - timedelta(days=3)
    period.closes_at = now - timedelta(days=1)


def test_register_student_enrolls_when_capacity_available(client, db_session: Session) -> None:
    seed = seed_registration_case(db_session)

    response = client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": str(seed["student_id"])},
        json={"section_id": seed["section_id"], "idempotency_key": "register-once"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "enrolled",
        "enrollment_id": 1,
        "section_id": seed["section_id"],
        "remaining_seats": 1,
    }


def test_registration_idempotency_returns_same_response(client, db_session: Session) -> None:
    seed = seed_registration_case(db_session)
    payload = {"section_id": seed["section_id"], "idempotency_key": "same-click"}

    first = client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": str(seed["student_id"])},
        json=payload,
    )
    second = client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": str(seed["student_id"])},
        json=payload,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == first.json()
    assert db_session.query(Enrollment).count() == 1


def test_registration_idempotency_conflicts_for_different_section(
    client,
    db_session: Session,
) -> None:
    seed = seed_registration_case(db_session)
    db_session.add(
        Section(
            id=2,
            course_offering_id=1,
            section_code="002",
            capacity=2,
            status="open",
        )
    )
    db_session.commit()

    first = client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": str(seed["student_id"])},
        json={"section_id": seed["section_id"], "idempotency_key": "same-key-diff-section"},
    )
    conflict = client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": str(seed["student_id"])},
        json={"section_id": 2, "idempotency_key": "same-key-diff-section"},
    )

    assert first.status_code == 200
    assert conflict.status_code == 409
    assert conflict.json()["error"] == "idempotency_conflict"


def test_registered_student_cannot_register_same_section_again(
    client,
    db_session: Session,
) -> None:
    seed = seed_registration_case(db_session)

    registered = client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": str(seed["student_id"])},
        json={"section_id": seed["section_id"], "idempotency_key": "first-registration"},
    )
    duplicate = client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": str(seed["student_id"])},
        json={"section_id": seed["section_id"], "idempotency_key": "second-registration"},
    )

    assert registered.status_code == 200
    assert duplicate.status_code == 409
    assert duplicate.json()["error"] == "duplicate_registration"
    assert db_session.query(Enrollment).filter_by(status="enrolled").count() == 1


def test_full_section_creates_waitlist_entry(client, db_session: Session) -> None:
    seed = seed_registration_case(db_session, section_capacity=1)
    add_manual_student(db_session, 2)
    db_session.commit()

    enrolled = client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": str(seed["student_id"])},
        json={"section_id": seed["section_id"], "idempotency_key": "first-seat"},
    )
    waitlisted = client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": "2"},
        json={"section_id": seed["section_id"], "idempotency_key": "second-seat"},
    )

    assert enrolled.status_code == 200
    assert enrolled.json()["status"] == "enrolled"
    assert waitlisted.status_code == 200
    assert waitlisted.json() == {"status": "waitlisted", "waitlist_entry_id": 1, "position": 1}
    assert db_session.query(Enrollment).filter_by(section_id=1, status="enrolled").count() == 1


def test_capacity_invariant_prevents_overbooking(client, db_session: Session) -> None:
    seed = seed_registration_case(db_session, section_capacity=1)
    for student_id in range(2, 7):
        add_manual_student(db_session, student_id)
    db_session.commit()

    for student_id in range(1, 7):
        response = client.post(
            "/api/v1/registrations",
            headers={"X-Student-Id": str(student_id)},
            json={
                "section_id": seed["section_id"],
                "idempotency_key": f"capacity-{student_id}",
            },
        )
        assert response.status_code == 200

    assert db_session.query(Enrollment).filter_by(status="enrolled").count() == 1
    assert db_session.query(WaitlistEntry).filter_by(status="waiting").count() == 5


def test_drop_registration_marks_enrollment_dropped(client, db_session: Session) -> None:
    seed = seed_registration_case(db_session)
    registered = client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": str(seed["student_id"])},
        json={"section_id": seed["section_id"], "idempotency_key": "drop-me-1"},
    )

    enrollment_id = registered.json()["enrollment_id"]
    response = client.delete(
        f"/api/v1/registrations/{enrollment_id}",
        headers={"X-Student-Id": str(seed["student_id"])},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "dropped",
        "enrollment_id": enrollment_id,
        "section_id": seed["section_id"],
        "promoted": None,
    }
    assert db_session.get(Enrollment, enrollment_id).status == "dropped"


def test_drop_registration_promotes_first_waitlisted_student(client, db_session: Session) -> None:
    seed = seed_registration_case(db_session, section_capacity=1)
    add_manual_student(db_session, 2)
    db_session.commit()

    registered = client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": str(seed["student_id"])},
        json={"section_id": seed["section_id"], "idempotency_key": "promote-first-seat"},
    )
    waitlisted = client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": "2"},
        json={"section_id": seed["section_id"], "idempotency_key": "promote-waiting-seat"},
    )

    response = client.delete(
        f"/api/v1/registrations/{registered.json()['enrollment_id']}",
        headers={"X-Student-Id": str(seed["student_id"])},
    )

    assert response.status_code == 200
    promoted = response.json()["promoted"]
    assert promoted["student_id"] == 2
    assert promoted["waitlist_entry_id"] == waitlisted.json()["waitlist_entry_id"]
    assert db_session.get(WaitlistEntry, promoted["waitlist_entry_id"]).status == "promoted"
    assert db_session.get(Enrollment, promoted["enrollment_id"]).student_id == 2
    assert db_session.query(Enrollment).filter_by(section_id=1, status="enrolled").count() == 1


def test_drop_skips_ineligible_waitlist_entry_and_promotes_next(
    client,
    db_session: Session,
) -> None:
    seed = seed_registration_case(db_session, section_capacity=1)
    add_manual_student(db_session, 2)
    add_manual_student(db_session, 3)
    db_session.commit()

    registered = client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": str(seed["student_id"])},
        json={"section_id": seed["section_id"], "idempotency_key": "skip-first-seat"},
    )
    first_waitlisted = client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": "2"},
        json={"section_id": seed["section_id"], "idempotency_key": "skip-waiting-one"},
    )
    second_waitlisted = client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": "3"},
        json={"section_id": seed["section_id"], "idempotency_key": "skip-waiting-two"},
    )
    db_session.get(Student, 2).academic_profile.academic_year = None
    db_session.commit()

    response = client.delete(
        f"/api/v1/registrations/{registered.json()['enrollment_id']}",
        headers={"X-Student-Id": str(seed["student_id"])},
    )

    assert response.status_code == 200
    assert response.json()["promoted"]["student_id"] == 3
    assert db_session.get(WaitlistEntry, first_waitlisted.json()["waitlist_entry_id"]).status == (
        "skipped"
    )
    assert db_session.get(WaitlistEntry, second_waitlisted.json()["waitlist_entry_id"]).status == (
        "promoted"
    )
    assert db_session.query(Enrollment).filter_by(section_id=1, status="enrolled").count() == 1


def test_drop_skips_waitlist_and_returns_no_promotion_when_no_student_is_eligible(
    client,
    db_session: Session,
) -> None:
    seed = seed_registration_case(db_session, section_capacity=1)
    add_manual_student(db_session, 2)
    db_session.commit()

    registered = client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": str(seed["student_id"])},
        json={"section_id": seed["section_id"], "idempotency_key": "no-promo-seat"},
    )
    waitlisted = client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": "2"},
        json={"section_id": seed["section_id"], "idempotency_key": "no-promo-waiting"},
    )
    db_session.get(Student, 2).academic_profile.academic_year = None
    db_session.commit()

    response = client.delete(
        f"/api/v1/registrations/{registered.json()['enrollment_id']}",
        headers={"X-Student-Id": str(seed["student_id"])},
    )

    assert response.status_code == 200
    assert response.json()["promoted"] is None
    assert db_session.get(WaitlistEntry, waitlisted.json()["waitlist_entry_id"]).status == (
        "skipped"
    )
    assert db_session.query(Enrollment).filter_by(section_id=1, status="enrolled").count() == 0


def test_waitlist_endpoints_join_list_and_cancel(client, db_session: Session) -> None:
    seed = seed_registration_case(db_session, section_capacity=1)
    add_manual_student(db_session, 2)
    db_session.commit()
    client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": str(seed["student_id"])},
        json={"section_id": seed["section_id"], "idempotency_key": "waitlist-api-seat"},
    )

    joined = client.post(
        "/api/v1/waitlists",
        headers={"X-Student-Id": "2"},
        json={"section_id": seed["section_id"]},
    )
    listed = client.get("/api/v1/waitlists/me", headers={"X-Student-Id": "2"})
    cancelled = client.delete(
        f"/api/v1/waitlists/{joined.json()['waitlist_entry_id']}",
        headers={"X-Student-Id": "2"},
    )
    rejoined = client.post(
        "/api/v1/waitlists",
        headers={"X-Student-Id": "2"},
        json={"section_id": seed["section_id"]},
    )

    assert joined.status_code == 200
    assert joined.json()["status"] == "waitlisted"
    assert listed.status_code == 200
    assert listed.json()[0]["waitlist_entry_id"] == joined.json()["waitlist_entry_id"]
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert rejoined.status_code == 200
    assert rejoined.json()["waitlist_entry_id"] == joined.json()["waitlist_entry_id"]
    assert db_session.get(WaitlistEntry, joined.json()["waitlist_entry_id"]).status == "waiting"


def test_student_cannot_cancel_another_students_waitlist_entry(
    client,
    db_session: Session,
) -> None:
    seed = seed_registration_case(db_session, section_capacity=1)
    add_manual_student(db_session, 2)
    add_manual_student(db_session, 3)
    db_session.commit()
    client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": str(seed["student_id"])},
        json={"section_id": seed["section_id"], "idempotency_key": "waitlist-owner-seat"},
    )
    joined = client.post(
        "/api/v1/waitlists",
        headers={"X-Student-Id": "2"},
        json={"section_id": seed["section_id"]},
    )

    response = client.delete(
        f"/api/v1/waitlists/{joined.json()['waitlist_entry_id']}",
        headers={"X-Student-Id": "3"},
    )

    assert response.status_code == 404
    assert response.json()["error"] == "not_found"
    assert db_session.get(WaitlistEntry, joined.json()["waitlist_entry_id"]).status == "waiting"


def test_duplicate_active_waitlist_join_returns_conflict(
    client,
    db_session: Session,
) -> None:
    seed = seed_registration_case(db_session, section_capacity=1)
    add_manual_student(db_session, 2)
    db_session.commit()
    client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": str(seed["student_id"])},
        json={"section_id": seed["section_id"], "idempotency_key": "waitlist-dupe-seat"},
    )

    first = client.post(
        "/api/v1/waitlists",
        headers={"X-Student-Id": "2"},
        json={"section_id": seed["section_id"]},
    )
    duplicate = client.post(
        "/api/v1/waitlists",
        headers={"X-Student-Id": "2"},
        json={"section_id": seed["section_id"]},
    )

    assert first.status_code == 200
    assert duplicate.status_code == 409
    assert duplicate.json()["error"] == "duplicate_registration"


def test_waitlist_join_requires_full_section(client, db_session: Session) -> None:
    seed = seed_registration_case(db_session, section_capacity=2)

    response = client.post(
        "/api/v1/waitlists",
        headers={"X-Student-Id": str(seed["student_id"])},
        json={"section_id": seed["section_id"]},
    )

    assert response.status_code == 409
    assert response.json()["error"] == "section_has_available_seats"


def test_registration_accepts_student_jwt(client, db_session: Session) -> None:
    seed = seed_registration_case(db_session)
    user = User(email="jwt.student@example.com", role="student")
    db_session.add(user)
    db_session.flush()
    db_session.get(Student, seed["student_id"]).user_id = user.id
    db_session.commit()
    token = create_access_token(user.id, "student")

    response = client.post(
        "/api/v1/registrations",
        headers={"Authorization": f"Bearer {token}"},
        json={"section_id": seed["section_id"], "idempotency_key": "jwt-register"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "enrolled"


def test_registration_requires_student_identity(client, db_session: Session) -> None:
    seed = seed_registration_case(db_session)

    response = client.post(
        "/api/v1/registrations",
        json={"section_id": seed["section_id"], "idempotency_key": "missing-student"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Provide a student bearer token or X-Student-Id header."


def test_registration_rejects_non_student_jwt(client, db_session: Session) -> None:
    seed = seed_registration_case(db_session)
    user = User(email="admin@example.com", role="admin")
    db_session.add(user)
    db_session.commit()
    token = create_access_token(user.id, "admin")

    response = client.post(
        "/api/v1/registrations",
        headers={"Authorization": f"Bearer {token}"},
        json={"section_id": seed["section_id"], "idempotency_key": "admin-register"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Students only."


def test_list_registrations_and_timetable(client, db_session: Session) -> None:
    seed = seed_registration_case(db_session)
    client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": str(seed["student_id"])},
        json={"section_id": seed["section_id"], "idempotency_key": "list-me-1"},
    )

    registrations = client.get(
        "/api/v1/registrations/me",
        headers={"X-Student-Id": str(seed["student_id"])},
    )
    timetable = client.get(
        "/api/v1/registrations/me/timetable",
        headers={"X-Student-Id": str(seed["student_id"])},
    )

    assert registrations.status_code == 200
    assert registrations.json()[0]["course_code"] == "CSE3010"
    assert timetable.status_code == 200
    assert timetable.json()[0]["day_of_week"] == "Monday"


def test_manual_profile_skips_gpa_rule(client, db_session: Session) -> None:
    seed = seed_registration_case(db_session, with_gpa_rule=True)

    response = client.get(
        f"/api/v1/sections/{seed['section_id']}/eligibility",
        headers={"X-Student-Id": str(seed["student_id"])},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["eligible"] is True
    assert body["gpa_rules_enabled"] is False
    assert {
        "rule": "gpa",
        "status": "skipped",
        "message": "GPA is skipped because the student profile is manual and not INS-verified.",
    } in body["checks"]


def test_full_section_eligibility_preview_skips_capacity_without_failure(
    client,
    db_session: Session,
) -> None:
    seed = seed_registration_case(db_session, section_capacity=1)
    add_manual_student(db_session, 2)
    db_session.commit()
    client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": str(seed["student_id"])},
        json={"section_id": seed["section_id"], "idempotency_key": "eligibility-seat"},
    )

    response = client.get(
        f"/api/v1/sections/{seed['section_id']}/eligibility",
        headers={"X-Student-Id": "2"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["eligible"] is True
    assert {
        "rule": "capacity",
        "status": "skipped",
        "message": "Section is full; eligible students can join the waitlist.",
    } in body["checks"]


def test_closed_registration_period_blocks_registration_and_waitlist_join(
    client,
    db_session: Session,
) -> None:
    seed = seed_registration_case(db_session, section_capacity=1)
    add_manual_student(db_session, 2)
    add_manual_student(db_session, 3)
    db_session.commit()
    client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": str(seed["student_id"])},
        json={"section_id": seed["section_id"], "idempotency_key": "closed-period-seat"},
    )
    close_registration_period(db_session)
    db_session.commit()

    registration = client.post(
        "/api/v1/registrations",
        headers={"X-Student-Id": "2"},
        json={"section_id": seed["section_id"], "idempotency_key": "closed-registration"},
    )
    waitlist = client.post(
        "/api/v1/waitlists",
        headers={"X-Student-Id": "3"},
        json={"section_id": seed["section_id"]},
    )

    assert registration.status_code == 400
    assert registration.json()["error"] == "registration_period_closed"
    assert waitlist.status_code == 400
    assert waitlist.json()["error"] == "registration_period_closed"
