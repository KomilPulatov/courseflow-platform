from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import (
    Course,
    CourseOffering,
    Department,
    Major,
    Professor,
    RegistrationPeriod,
    Room,
    RoomAllocation,
    Section,
    SectionSchedule,
    Semester,
    User,
)
from app.modules.professors.errors import RoomCapacityError, RoomNotInPoolError
from app.modules.professors.service import ProfessorService

# ── Seed helper ───────────────────────────────────────────────────────────────


def seed_professor_rooms_case(db: Session, *, section_capacity: int = 30) -> dict:
    """Insert the minimum data needed for professor-room tests."""
    now = datetime.now(UTC)

    dept = Department(id=1, code="CSE", name="Computer Science")
    major = Major(id=1, department_id=1, code="SE", name="Software Engineering")
    semester = Semester(id=1, name="Spring 2026", status="active")
    course = Course(id=1, department_id=1, code="CSE3010", title="Databases", credits=3)
    offering = CourseOffering(id=1, course_id=1, semester_id=1, status="active")

    prof_user = User(
        id=10,
        email="prof@test.example.com",
        password_hash=hash_password("password123"),
        role="professor",
        status="active",
    )
    professor = Professor(id=1, user_id=10, full_name="Dr. Test", department_name="CSE")

    section = Section(
        id=1,
        course_offering_id=1,
        professor_id=1,
        section_code="001",
        capacity=section_capacity,
        room_selection_mode="professor_choice",
        status="open",
    )
    schedule = SectionSchedule(
        id=1,
        section_id=1,
        day_of_week="Monday",
        start_time="09:00",
        end_time="10:30",
    )
    period = RegistrationPeriod(
        id=1,
        semester_id=1,
        opens_at=now - timedelta(days=1),
        closes_at=now + timedelta(days=1),
        status="open",
    )

    room_large = Room(
        id=1, building="A", room_number="101", capacity=40, room_type="lecture", is_active=True
    )
    room_small = Room(
        id=2, building="A", room_number="102", capacity=20, room_type="lecture", is_active=True
    )

    alloc_large = RoomAllocation(
        id=1, section_id=1, room_id=1, allocated_by_user_id=None, is_preferred=False
    )

    db.add_all(
        [
            dept,
            major,
            semester,
            course,
            offering,
            prof_user,
            professor,
            section,
            schedule,
            period,
            room_large,
            room_small,
            alloc_large,
        ]
    )
    db.commit()

    return {
        "prof_user_id": prof_user.id,
        "professor_id": professor.id,
        "section_id": section.id,
        "room_large_id": room_large.id,
        "room_small_id": room_small.id,
    }


def _get_professor_token(
    client, email: str = "prof@test.example.com", password: str = "password123"
) -> str:
    resp = client.post(
        "/api/v1/auth/professor/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


# ── Unit tests: validation logic ──────────────────────────────────────────────


def test_room_validation_rejects_room_not_in_pool(db_session: Session) -> None:
    seed = seed_professor_rooms_case(db_session)
    service = ProfessorService(db_session)

    from app.modules.professors.schemas import RoomPreferenceCreate

    with pytest.raises(RoomNotInPoolError):
        service.save_room_preference(
            user_id=seed["prof_user_id"],
            section_id=seed["section_id"],
            data=RoomPreferenceCreate(room_id=seed["room_small_id"], preference_rank=1),
        )


def test_room_validation_rejects_small_room(db_session: Session) -> None:
    seed = seed_professor_rooms_case(db_session, section_capacity=30)
    db_session.add(
        RoomAllocation(
            section_id=seed["section_id"],
            room_id=seed["room_small_id"],
            allocated_by_user_id=None,
            is_preferred=False,
        )
    )
    db_session.commit()

    service = ProfessorService(db_session)
    from app.modules.professors.schemas import RoomPreferenceCreate

    with pytest.raises(RoomCapacityError):
        service.save_room_preference(
            user_id=seed["prof_user_id"],
            section_id=seed["section_id"],
            data=RoomPreferenceCreate(room_id=seed["room_small_id"], preference_rank=1),
        )


# ── API integration tests ─────────────────────────────────────────────────────


def test_professor_lists_assigned_sections(client, db_session: Session) -> None:
    seed = seed_professor_rooms_case(db_session)
    token = _get_professor_token(client)

    resp = client.get(
        "/api/v1/professor/sections",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    sections = resp.json()
    assert len(sections) == 1
    assert sections[0]["section_id"] == seed["section_id"]
    assert sections[0]["room_selection_mode"] == "professor_choice"


def test_professor_selects_room_successfully(client, db_session: Session) -> None:
    seed = seed_professor_rooms_case(db_session)
    token = _get_professor_token(client)
    section_id = seed["section_id"]
    room_id = seed["room_large_id"]

    options_resp = client.get(
        f"/api/v1/professor/sections/{section_id}/room-options",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert options_resp.status_code == 200
    options = options_resp.json()["options"]
    assert any(o["room_id"] == room_id for o in options)

    pref_resp = client.post(
        f"/api/v1/professor/sections/{section_id}/room-preferences",
        json={"room_id": room_id, "preference_rank": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert pref_resp.status_code == 200
    body = pref_resp.json()
    assert body["status"] == "selected"
    assert body["room_id"] == room_id


def test_admin_creates_suggestion_run(client, db_session: Session) -> None:
    seed_professor_rooms_case(db_session)

    admin_user = User(
        id=99,
        email="admin@test.example.com",
        password_hash=hash_password("admin12345"),
        role="admin",
        status="active",
    )
    db_session.add(admin_user)
    db_session.commit()

    admin_login = client.post(
        "/api/v1/auth/admin/login",
        json={"email": "admin@test.example.com", "password": "admin12345"},
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]

    run_resp = client.post(
        "/api/v1/admin/scheduling/suggestion-runs",
        json={"semester_id": 1, "strategy": "balanced_heuristic"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert run_resp.status_code == 201
    run = run_resp.json()
    assert run["status"] == "completed"
    run_id = run["run_id"]

    get_resp = client.get(
        f"/api/v1/admin/scheduling/suggestion-runs/{run_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert get_resp.status_code == 200
    run_detail = get_resp.json()
    assert run_detail["id"] == run_id
    assert run_detail["semester_id"] == 1
    assert isinstance(run_detail["items"], list)
    assert len(run_detail["items"]) >= 1
