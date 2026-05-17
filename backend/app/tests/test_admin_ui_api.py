from app.core.security import create_access_token, hash_password
from app.db.models import Course, Semester, User


def create_admin_headers(db_session) -> dict[str, str]:
    admin = User(
        email="admin.ui@example.com",
        password_hash=hash_password("secret123"),
        role="admin",
        status="active",
    )
    db_session.add(admin)
    db_session.commit()
    token = create_access_token(admin.id, "admin")
    return {"Authorization": f"Bearer {token}"}


def test_admin_spa_routes_return_index_html(client) -> None:
    dashboard = client.get("/admin")
    nested = client.get("/admin/courses/42/prerequisites")
    script = client.get("/admin/assets/app.js")

    assert dashboard.status_code == 200
    assert nested.status_code == 200
    assert script.status_code == 200
    assert "CRSP Admin" in dashboard.text
    assert "CRSP Admin" in nested.text
    assert "application/javascript" in script.headers["content-type"]


def test_admin_can_list_course_eligibility_rules(client, db_session) -> None:
    headers = create_admin_headers(db_session)
    course = Course(code="CSE4010", title="Distributed Systems", credits=3)
    db_session.add(course)
    db_session.commit()

    created = client.post(
        f"/api/v1/admin/courses/{course.id}/eligibility-rules",
        headers=headers,
        json={
            "min_academic_year": 3,
            "min_gpa": 3.25,
            "allowed_department_ids": [1, 2],
            "allowed_major_ids": [4],
            "rule_metadata": {"source": "test"},
        },
    )
    listed = client.get(
        f"/api/v1/admin/courses/{course.id}/eligibility-rules",
        headers=headers,
    )

    assert created.status_code == 201
    assert listed.status_code == 200
    assert listed.json() == [
        {
            "id": created.json()["id"],
            "course_id": course.id,
            "min_academic_year": 3,
            "min_gpa": 3.25,
            "allowed_department_ids": [1, 2],
            "allowed_major_ids": [4],
            "rule_metadata": {"source": "test"},
        }
    ]


def test_admin_can_list_recent_scheduling_runs(client, db_session) -> None:
    headers = create_admin_headers(db_session)
    semester = Semester(name="Spring 2027", status="active")
    db_session.add(semester)
    db_session.commit()

    first = client.post(
        "/api/v1/admin/scheduling/suggestion-runs",
        headers=headers,
        json={"semester_id": semester.id, "strategy": "balanced_heuristic"},
    )
    second = client.post(
        "/api/v1/admin/scheduling/suggestion-runs",
        headers=headers,
        json={"semester_id": semester.id, "strategy": "balanced_heuristic"},
    )
    listed = client.get(
        "/api/v1/admin/scheduling/suggestion-runs",
        headers=headers,
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert listed.status_code == 200
    assert [run["id"] for run in listed.json()[:2]] == [
        second.json()["run_id"],
        first.json()["run_id"],
    ]
