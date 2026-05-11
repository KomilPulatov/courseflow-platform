from datetime import UTC, datetime, timedelta

from app.core.security import create_access_token, hash_password
from app.db.models import Course, CoursePrerequisite, Department, Major, Semester, User


def create_admin_headers(db_session) -> dict[str, str]:
    admin = User(
        email="admin@example.com",
        password_hash=hash_password("secret123"),
        role="admin",
        status="active",
    )
    db_session.add(admin)
    db_session.commit()
    token = create_access_token(admin.id, "admin")
    return {"Authorization": f"Bearer {token}"}


def test_admin_setup_and_public_catalog_flow(client, db_session) -> None:
    headers = create_admin_headers(db_session)

    department = client.post(
        "/api/v1/admin/departments",
        headers=headers,
        json={"code": "CSE", "name": "Computer Science"},
    )
    assert department.status_code == 201
    department_id = department.json()["id"]

    major = client.post(
        "/api/v1/admin/majors",
        headers=headers,
        json={"department_id": department_id, "code": "SE", "name": "Software Engineering"},
    )
    assert major.status_code == 201

    semester = client.post(
        "/api/v1/admin/semesters",
        headers=headers,
        json={"name": "Spring 2026", "status": "active"},
    )
    assert semester.status_code == 201
    semester_id = semester.json()["id"]

    prerequisite_course = client.post(
        "/api/v1/admin/courses",
        headers=headers,
        json={
            "department_id": department_id,
            "code": "CSE2010",
            "title": "Programming",
            "credits": 3,
        },
    )
    assert prerequisite_course.status_code == 201
    prerequisite_course_id = prerequisite_course.json()["id"]

    target_course = client.post(
        "/api/v1/admin/courses",
        headers=headers,
        json={
            "department_id": department_id,
            "code": "CSE3010",
            "title": "Database Application Design",
            "credits": 3,
            "description": "Transactional systems and schema design.",
            "course_type": "core",
        },
    )
    assert target_course.status_code == 201
    target_course_id = target_course.json()["id"]

    prerequisites = client.put(
        f"/api/v1/admin/courses/{target_course_id}/prerequisites",
        headers=headers,
        json={"prerequisite_course_ids": [prerequisite_course_id], "rule_group": "all"},
    )
    assert prerequisites.status_code == 200
    assert prerequisites.json()[0]["prerequisite_code"] == "CSE2010"

    offering = client.post(
        "/api/v1/admin/course-offerings",
        headers=headers,
        json={"course_id": target_course_id, "semester_id": semester_id, "status": "active"},
    )
    assert offering.status_code == 201
    offering_id = offering.json()["id"]

    section = client.post(
        "/api/v1/admin/sections",
        headers=headers,
        json={
            "course_offering_id": offering_id,
            "section_code": "001",
            "capacity": 30,
            "room_selection_mode": "professor_choice",
            "status": "open",
        },
    )
    assert section.status_code == 201
    section_id = section.json()["id"]

    period = client.post(
        "/api/v1/admin/registration-periods",
        headers=headers,
        json={
            "semester_id": semester_id,
            "opens_at": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
            "closes_at": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
            "status": "open",
        },
    )
    assert period.status_code == 201

    courses = client.get("/api/v1/courses", params={"semester_id": semester_id})
    assert courses.status_code == 200
    assert courses.json()[0]["code"] == "CSE3010"

    course_detail = client.get(f"/api/v1/courses/{target_course_id}")
    assert course_detail.status_code == 200
    assert course_detail.json()["prerequisites"][0]["code"] == "CSE2010"

    sections = client.get(
        f"/api/v1/courses/{target_course_id}/sections", params={"semester_id": semester_id}
    )
    assert sections.status_code == 200
    assert sections.json()[0]["section_code"] == "001"

    section_detail = client.get(f"/api/v1/sections/{section_id}")
    assert section_detail.status_code == 200
    assert section_detail.json()["remaining_seats"] == 30

    availability = client.get(f"/api/v1/sections/{section_id}/availability")
    assert availability.status_code == 200
    assert availability.json()["remaining_seats"] == 30


def test_prerequisite_cycle_is_rejected(client, db_session) -> None:
    headers = create_admin_headers(db_session)
    department = Department(code="CSE", name="Computer Science")
    db_session.add(department)
    db_session.flush()
    course_a = Course(department_id=department.id, code="CSE1001", title="A", credits=3)
    course_b = Course(department_id=department.id, code="CSE1002", title="B", credits=3)
    db_session.add_all([course_a, course_b])
    db_session.flush()
    db_session.add(CoursePrerequisite(course_id=course_a.id, prerequisite_course_id=course_b.id))
    db_session.commit()

    response = client.put(
        f"/api/v1/admin/courses/{course_b.id}/prerequisites",
        headers=headers,
        json={"prerequisite_course_ids": [course_a.id], "rule_group": "all"},
    )

    assert response.status_code == 409
    assert "cycle" in response.json()["detail"].lower()


def test_eligible_only_requires_student_header(client, db_session) -> None:
    department = Department(id=1, code="CSE", name="Computer Science")
    major = Major(id=1, department_id=1, code="SE", name="Software Engineering")
    semester = Semester(id=1, name="Spring 2026", status="active")
    course = Course(id=1, department_id=1, code="CSE3010", title="Databases", credits=3)
    db_session.add_all([department, major, semester, course])
    db_session.commit()

    response = client.get("/api/v1/courses", params={"eligible_only": "true"})

    assert response.status_code == 400
    assert "X-Student-Id" in response.json()["detail"]
