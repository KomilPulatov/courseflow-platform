from sqlalchemy.orm import Session

from app.db.models import Department, ExternalAccount, Major, Student, StudentAcademicProfile, User


def test_manual_student_start_creates_user_and_incomplete_profile(
    client,
    db_session: Session,
) -> None:
    response = client.post(
        "/api/v1/auth/student/manual-start",
        json={
            "student_number": "2310204",
            "full_name": "Manual Student",
            "email": "manual.student@example.com",
            "password": "secret123",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["role"] == "student"
    assert body["profile_source"] == "manual"
    assert body["requires_profile_completion"] is True
    assert body["access_token"]

    user = db_session.query(User).filter_by(email="manual.student@example.com").one()
    student = db_session.query(Student).filter_by(user_id=user.id).one()
    profile = db_session.query(StudentAcademicProfile).filter_by(student_id=student.id).one()

    assert user.role == "student"
    assert student.student_number == "2310204"
    assert student.profile_source == "manual"
    assert profile.gpa_is_verified is False


def test_manual_student_start_rejects_duplicate_student_number(
    client,
    db_session: Session,
) -> None:
    db_session.add(
        Student(
            student_number="2310204",
            full_name="Existing Student",
            profile_source="manual",
        )
    )
    db_session.commit()

    response = client.post(
        "/api/v1/auth/student/manual-start",
        json={
            "student_number": "2310204",
            "full_name": "Manual Student",
            "email": "manual.student@example.com",
            "password": "secret123",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "A student with this student number already exists."


def test_manual_student_can_complete_profile_with_catalog_ids(client, db_session: Session) -> None:
    db_session.add(Department(id=1, code="CSE", name="Computer Science"))
    db_session.add(Major(id=1, department_id=1, code="SE", name="Software Engineering"))
    db_session.commit()
    created = client.post(
        "/api/v1/auth/student/manual-start",
        json={
            "student_number": "2310205",
            "full_name": "Manual Student",
            "email": "manual.profile@example.com",
            "password": "secret123",
        },
    )

    response = client.put(
        "/api/v1/student-profiles/me/manual",
        headers={"Authorization": f"Bearer {created.json()['access_token']}"},
        json={
            "department_id": 1,
            "major_id": 1,
            "academic_year": 3,
            "completed_course_codes": ["MSC1010"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["academic_profile"]["department_id"] == 1
    assert body["academic_profile"]["major_id"] == 1
    assert body["academic_profile"]["department_name"] == "Computer Science"
    assert body["completed_courses"][0]["course_code"] == "MSC1010"


def test_ins_login_syncs_verified_profile(client, db_session: Session, monkeypatch) -> None:
    def fake_run_sync_simple(db: Session, user_id: str, username: str, password: str) -> None:
        student = db.query(Student).filter(Student.user_id == int(user_id)).one()
        student.full_name = f"INS Student {username}"

        profile = (
            db.query(StudentAcademicProfile)
            .filter(StudentAcademicProfile.student_id == student.id)
            .first()
        )
        if profile is None:
            profile = StudentAcademicProfile(
                student_id=student.id,
                department_name="ICE",
                major_name="Information and Computer Engineering",
                academic_year=3,
                current_gpa=4.2,
                gpa_is_verified=True,
                academic_status="active",
            )
            db.add(profile)
        else:
            profile.department_name = "ICE"
            profile.major_name = "Information and Computer Engineering"
            profile.academic_year = 3
            profile.current_gpa = 4.2
            profile.gpa_is_verified = True
            profile.academic_status = "active"

        db.flush()

    monkeypatch.setattr("app.modules.auth.service.run_sync_simple", fake_run_sync_simple)

    response = client.post(
        "/api/v1/auth/student/ins-login",
        json={"student_number": "U2310037", "password": "U2310037"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "student"
    assert body["profile_source"] == "ins_verified"
    assert body["gpa_is_verified"] is True
    assert body["access_token"]

    student = db_session.query(Student).filter_by(student_number="U2310037").one()
    profile = db_session.query(StudentAcademicProfile).filter_by(student_id=student.id).one()
    external_account = db_session.query(ExternalAccount).filter_by(student_id=student.id).one()

    assert student.profile_source == "ins_verified"
    assert profile.department_name == "ICE"
    assert profile.gpa_is_verified is True
    assert external_account.provider == "ins"


def test_ins_login_rejects_invalid_password(client, monkeypatch) -> None:
    def fake_run_sync_simple(db: Session, user_id: str, username: str, password: str) -> None:
        raise Exception("Login failed.")

    monkeypatch.setattr("app.modules.auth.service.run_sync_simple", fake_run_sync_simple)

    response = client.post(
        "/api/v1/auth/student/ins-login",
        json={"student_number": "U2310037", "password": "wrong"},
    )

    assert response.status_code == 401
