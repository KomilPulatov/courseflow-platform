from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.models import Course, CourseOffering, Professor, Section, Semester, User


def admin_headers(db_session: Session) -> dict[str, str]:
    user = User(email="admin.rooms@example.com", role="admin", status="active")
    db_session.add(user)
    db_session.commit()
    return {"Authorization": f"Bearer {create_access_token(user.id, 'admin')}"}


def test_admin_professor_room_allocation_and_scheduling(client, db_session: Session) -> None:
    headers = admin_headers(db_session)
    semester = Semester(id=1, name="Spring 2026", status="active")
    course = Course(id=1, code="CSE3010", title="Databases", credits=3)
    offering = CourseOffering(id=1, course_id=1, semester_id=1, status="active")
    db_session.add_all([semester, course, offering])
    db_session.commit()

    professor_response = client.post(
        "/api/v1/admin/professors",
        headers=headers,
        json={
            "email": "prof.rooms@example.com",
            "full_name": "Room Professor",
            "password": "prof12345",
        },
    )
    assert professor_response.status_code == 201
    professor_id = professor_response.json()["id"]

    section_response = client.post(
        "/api/v1/admin/sections",
        headers=headers,
        json={
            "course_offering_id": 1,
            "professor_id": professor_id,
            "section_code": "001",
            "capacity": 30,
            "room_selection_mode": "professor_choice",
            "status": "open",
        },
    )
    assert section_response.status_code == 201
    section_id = section_response.json()["id"]

    room_response = client.post(
        "/api/v1/admin/rooms",
        headers=headers,
        json={
            "building": "B",
            "room_number": "305",
            "capacity": 40,
            "room_type": "lecture",
        },
    )
    assert room_response.status_code == 201
    room_id = room_response.json()["id"]

    allocation_response = client.post(
        f"/api/v1/admin/sections/{section_id}/room-allocations",
        headers=headers,
        json={"room_ids": [room_id], "notes": "Demo room"},
    )
    assert allocation_response.status_code == 201
    assert allocation_response.json()[0]["room_id"] == room_id

    run_response = client.post(
        "/api/v1/admin/scheduling/suggestion-runs",
        headers=headers,
        json={"semester_id": 1, "strategy": "balanced_heuristic"},
    )
    assert run_response.status_code == 201
    run_id = run_response.json()["run_id"]

    detail_response = client.get(
        f"/api/v1/admin/scheduling/suggestion-runs/{run_id}", headers=headers
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["items"][0]["section_id"] == section_id

    approve_response = client.post(
        f"/api/v1/admin/scheduling/suggestion-runs/{run_id}/approve",
        headers=headers,
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"


def test_professor_can_choose_allocated_room(client, db_session: Session) -> None:
    admin = User(id=1, email="admin.prof@example.com", role="admin", status="active")
    professor_user = User(id=2, email="prof.pick@example.com", role="professor", status="active")
    professor = Professor(id=1, user_id=2, full_name="Professor Pick")
    semester = Semester(id=1, name="Spring 2026", status="active")
    course = Course(id=1, code="CSE3010", title="Databases", credits=3)
    offering = CourseOffering(id=1, course_id=1, semester_id=1, status="active")
    section = Section(
        id=1,
        course_offering_id=1,
        professor_id=1,
        section_code="001",
        capacity=30,
        room_selection_mode="professor_choice",
        status="open",
    )
    db_session.add_all([admin, professor_user, professor, semester, course, offering, section])
    db_session.commit()
    admin_headers_value = {"Authorization": f"Bearer {create_access_token(admin.id, 'admin')}"}
    professor_headers = {
        "Authorization": f"Bearer {create_access_token(professor_user.id, 'professor')}"
    }

    room = client.post(
        "/api/v1/admin/rooms",
        headers=admin_headers_value,
        json={"building": "A", "room_number": "101", "capacity": 35},
    ).json()
    client.post(
        "/api/v1/admin/sections/1/room-allocations",
        headers=admin_headers_value,
        json={"room_ids": [room["id"]]},
    )

    options = client.get("/api/v1/professor/sections/1/room-options", headers=professor_headers)
    assert options.status_code == 200
    assert options.json()["options"][0]["room_id"] == room["id"]

    choice = client.post(
        "/api/v1/professor/sections/1/room-preferences",
        headers=professor_headers,
        json={"room_id": room["id"], "preference_rank": 1},
    )
    assert choice.status_code == 200
    assert choice.json()["status"] == "selected"
