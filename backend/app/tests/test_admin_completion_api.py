from app.core.security import create_access_token, hash_password
from app.db.models import (
    Course,
    CourseOffering,
    Department,
    Enrollment,
    Major,
    Professor,
    ProfessorRoomPreference,
    Room,
    RoomAllocation,
    Section,
    Semester,
    Student,
    User,
)


def create_admin_headers(db_session) -> dict[str, str]:
    admin = User(
        email="admin.completion@example.com",
        password_hash=hash_password("secret123"),
        role="admin",
        status="active",
    )
    db_session.add(admin)
    db_session.commit()
    token = create_access_token(admin.id, "admin")
    return {"Authorization": f"Bearer {token}"}


def seed_catalog_chain(db_session) -> dict[str, int]:
    department = Department(code="CSE", name="Computer Science")
    db_session.add(department)
    db_session.flush()
    major = Major(department_id=department.id, code="SE", name="Software Engineering")
    semester = Semester(name="Spring 2028", status="active")
    course = Course(
        department_id=department.id,
        code="CSE4010",
        title="Distributed Systems",
        credits=3,
    )
    db_session.add_all([major, semester, course])
    db_session.flush()
    offering = CourseOffering(course_id=course.id, semester_id=semester.id, status="active")
    db_session.add(offering)
    db_session.flush()
    section = Section(
        course_offering_id=offering.id,
        section_code="001",
        capacity=30,
        room_selection_mode="admin_fixed",
        status="open",
    )
    db_session.add(section)
    db_session.commit()
    return {
        "department_id": department.id,
        "major_id": major.id,
        "semester_id": semester.id,
        "course_id": course.id,
        "offering_id": offering.id,
        "section_id": section.id,
    }


def test_archive_flow_requires_active_dependents_to_be_retired(client, db_session) -> None:
    headers = create_admin_headers(db_session)
    seeded = seed_catalog_chain(db_session)

    blocked_department = client.patch(
        f"/api/v1/admin/departments/{seeded['department_id']}",
        headers=headers,
        json={"is_active": False},
    )
    blocked_course = client.patch(
        f"/api/v1/admin/courses/{seeded['course_id']}",
        headers=headers,
        json={"is_active": False},
    )
    blocked_offering = client.patch(
        f"/api/v1/admin/course-offerings/{seeded['offering_id']}",
        headers=headers,
        json={"status": "archived"},
    )

    assert blocked_department.status_code == 409
    assert blocked_course.status_code == 409
    assert blocked_offering.status_code == 409

    closed_section = client.patch(
        f"/api/v1/admin/sections/{seeded['section_id']}",
        headers=headers,
        json={"status": "closed"},
    )
    archived_offering = client.patch(
        f"/api/v1/admin/course-offerings/{seeded['offering_id']}",
        headers=headers,
        json={"status": "archived"},
    )
    archived_course = client.patch(
        f"/api/v1/admin/courses/{seeded['course_id']}",
        headers=headers,
        json={"is_active": False},
    )
    archived_major = client.patch(
        f"/api/v1/admin/majors/{seeded['major_id']}",
        headers=headers,
        json={"is_active": False},
    )
    archived_department = client.patch(
        f"/api/v1/admin/departments/{seeded['department_id']}",
        headers=headers,
        json={"is_active": False},
    )

    assert closed_section.status_code == 200
    assert archived_offering.status_code == 200
    assert archived_course.status_code == 200
    assert archived_major.status_code == 200
    assert archived_department.status_code == 200
    assert archived_department.json()["is_active"] is False


def test_section_capacity_cannot_drop_below_active_enrollment(client, db_session) -> None:
    headers = create_admin_headers(db_session)
    seeded = seed_catalog_chain(db_session)
    first_student = Student(
        student_number="2028001",
        full_name="Capacity Student One",
        profile_source="manual",
    )
    second_student = Student(
        student_number="2028002",
        full_name="Capacity Student Two",
        profile_source="manual",
    )
    db_session.add_all([first_student, second_student])
    db_session.flush()
    db_session.add_all(
        [
            Enrollment(
                student_id=first_student.id,
                section_id=seeded["section_id"],
                course_id=seeded["course_id"],
                semester_id=seeded["semester_id"],
                status="enrolled",
            ),
            Enrollment(
                student_id=second_student.id,
                section_id=seeded["section_id"],
                course_id=seeded["course_id"],
                semester_id=seeded["semester_id"],
                status="enrolled",
            ),
        ]
    )
    db_session.commit()

    invalid_capacity = client.patch(
        f"/api/v1/admin/sections/{seeded['section_id']}",
        headers=headers,
        json={"capacity": 0},
    )
    below_enrollment = client.patch(
        f"/api/v1/admin/sections/{seeded['section_id']}",
        headers=headers,
        json={"capacity": 1},
    )
    exact_capacity = client.patch(
        f"/api/v1/admin/sections/{seeded['section_id']}",
        headers=headers,
        json={"capacity": 2},
    )

    assert invalid_capacity.status_code == 422
    assert below_enrollment.status_code == 409
    assert exact_capacity.status_code == 200


def test_selected_room_allocation_must_be_cleared_before_deallocation(client, db_session) -> None:
    headers = create_admin_headers(db_session)
    seeded = seed_catalog_chain(db_session)
    professor_user = User(
        email="prof.completion@example.com",
        password_hash=hash_password("secret123"),
        role="professor",
        status="active",
    )
    db_session.add(professor_user)
    db_session.flush()
    professor = Professor(user_id=professor_user.id, full_name="Dr. Completion")
    room = Room(building="A", room_number="201", capacity=40, room_type="lecture")
    db_session.add_all([professor, room])
    db_session.flush()
    section = db_session.get(Section, seeded["section_id"])
    section.professor_id = professor.id
    allocation = RoomAllocation(section_id=section.id, room_id=room.id)
    db_session.add(allocation)
    db_session.flush()
    db_session.add(
        ProfessorRoomPreference(
            section_id=section.id,
            professor_id=professor.id,
            room_id=room.id,
            preference_rank=1,
            status="selected",
        )
    )
    db_session.commit()

    blocked = client.delete(
        f"/api/v1/admin/sections/{section.id}/room-allocations/{room.id}",
        headers=headers,
    )
    preference = db_session.query(ProfessorRoomPreference).one()
    preference.status = "cancelled"
    db_session.commit()
    removed = client.delete(
        f"/api/v1/admin/sections/{section.id}/room-allocations/{room.id}",
        headers=headers,
    )

    assert blocked.status_code == 409
    assert removed.status_code == 204


def test_admin_can_update_and_delete_eligibility_rules(client, db_session) -> None:
    headers = create_admin_headers(db_session)
    course = Course(code="CSE4990", title="Capstone", credits=3)
    db_session.add(course)
    db_session.commit()

    created = client.post(
        f"/api/v1/admin/courses/{course.id}/eligibility-rules",
        headers=headers,
        json={"min_academic_year": 3},
    )
    updated = client.patch(
        f"/api/v1/admin/courses/{course.id}/eligibility-rules/{created.json()['id']}",
        headers=headers,
        json={"min_academic_year": 4, "min_gpa": 3.5},
    )
    removed = client.delete(
        f"/api/v1/admin/courses/{course.id}/eligibility-rules/{created.json()['id']}",
        headers=headers,
    )
    listed = client.get(
        f"/api/v1/admin/courses/{course.id}/eligibility-rules",
        headers=headers,
    )

    assert created.status_code == 201
    assert updated.status_code == 200
    assert updated.json()["min_academic_year"] == 4
    assert updated.json()["min_gpa"] == 3.5
    assert removed.status_code == 204
    assert listed.json() == []
