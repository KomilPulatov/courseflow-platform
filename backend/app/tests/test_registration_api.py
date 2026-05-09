from sqlalchemy.orm import Session

from app.db.models import Enrollment, Student, StudentAcademicProfile, WaitlistEntry
from app.tests.factories import seed_registration_case


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


def test_full_section_creates_waitlist_entry(client, db_session: Session) -> None:
    seed = seed_registration_case(db_session, section_capacity=1)
    db_session.add(
        Student(
            id=2,
            student_number="2310999",
            full_name="Second Student",
            profile_source="manual",
        )
    )
    db_session.add(
        StudentAcademicProfile(
            student_id=2,
            department_id=1,
            major_id=1,
            academic_year=3,
            gpa_is_verified=False,
        )
    )
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


def test_capacity_invariant_prevents_overbooking(client, db_session: Session) -> None:
    seed = seed_registration_case(db_session, section_capacity=1)
    for student_id in range(2, 7):
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
    }
    assert db_session.get(Enrollment, enrollment_id).status == "dropped"


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
