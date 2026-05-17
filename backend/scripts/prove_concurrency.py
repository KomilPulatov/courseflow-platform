# ruff: noqa: E402
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import delete, select

from app.core.config import settings
from app.db import models
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.modules.registration.errors import RegistrationError
from app.modules.registration.schemas import RegistrationCreate
from app.modules.registration.service import RegistrationService

DEMO_ID = 910001
STUDENT_IDS = list(range(DEMO_ID, DEMO_ID + 10))


def main() -> int:
    if not settings.DATABASE_URL.startswith("postgresql"):
        print("Concurrency proof must use PostgreSQL because SQLite ignores row-level locks.")
        print(f"Current DATABASE_URL is: {settings.DATABASE_URL}")
        return 1

    Base.metadata.create_all(bind=engine)
    reset_demo_data()
    seed_demo_data()

    with ThreadPoolExecutor(max_workers=len(STUDENT_IDS)) as executor:
        futures = [executor.submit(register_student, student_id) for student_id in STUDENT_IDS]
        results = [future.result() for future in as_completed(futures)]

    enrolled = [item for item in results if item["status"] == "enrolled"]
    waitlisted = [item for item in results if item["status"] == "waitlisted"]
    failed = [item for item in results if item["status"] == "failed"]

    with SessionLocal() as db:
        enrolled_count = (
            db.execute(
                select(models.Enrollment).where(
                    models.Enrollment.section_id == DEMO_ID,
                    models.Enrollment.status == "enrolled",
                )
            )
            .scalars()
            .all()
        )

    print("Concurrent registration proof")
    print(f"Students attempted: {len(STUDENT_IDS)}")
    print(f"Enrolled responses: {len(enrolled)}")
    print(f"Waitlisted responses: {len(waitlisted)}")
    print(f"Failed responses: {len(failed)}")
    print(f"Database enrolled rows: {len(enrolled_count)}")
    print("Expected: exactly 1 enrolled row because section capacity is 1.")

    if len(enrolled_count) != 1:
        return 2
    return 0


def register_student(student_id: int) -> dict[str, object]:
    with SessionLocal() as db:
        payload = RegistrationCreate(
            section_id=DEMO_ID,
            idempotency_key=f"concurrency-proof-{student_id}",
        )
        try:
            result = RegistrationService(db).register(student_id, payload)
        except RegistrationError as exc:
            return {"student_id": student_id, "status": "failed", "error": exc.code}

    status = "enrolled" if "enrollment_id" in result else "waitlisted"
    return {"student_id": student_id, "status": status, "result": result}


def reset_demo_data() -> None:
    with SessionLocal() as db:
        db.execute(delete(models.AuditLog).where(models.AuditLog.actor_student_id.in_(STUDENT_IDS)))
        db.execute(
            delete(models.RegistrationEvent).where(models.RegistrationEvent.section_id == DEMO_ID)
        )
        db.execute(
            delete(models.RegistrationIdempotencyKey).where(
                models.RegistrationIdempotencyKey.student_id.in_(STUDENT_IDS)
            )
        )
        db.execute(delete(models.WaitlistEntry).where(models.WaitlistEntry.section_id == DEMO_ID))
        db.execute(delete(models.Enrollment).where(models.Enrollment.section_id == DEMO_ID))
        db.execute(
            delete(models.StudentAcademicProfile).where(
                models.StudentAcademicProfile.student_id.in_(STUDENT_IDS)
            )
        )
        db.execute(delete(models.Student).where(models.Student.id.in_(STUDENT_IDS)))
        db.execute(
            delete(models.SectionSchedule).where(models.SectionSchedule.section_id == DEMO_ID)
        )
        db.execute(
            delete(models.RegistrationPeriod).where(
                models.RegistrationPeriod.semester_id == DEMO_ID
            )
        )
        db.execute(delete(models.Section).where(models.Section.id == DEMO_ID))
        db.execute(delete(models.CourseOffering).where(models.CourseOffering.id == DEMO_ID))
        db.execute(delete(models.Course).where(models.Course.id == DEMO_ID))
        db.execute(delete(models.Semester).where(models.Semester.id == DEMO_ID))
        db.execute(delete(models.Major).where(models.Major.id == DEMO_ID))
        db.execute(delete(models.Department).where(models.Department.id == DEMO_ID))
        db.commit()


def seed_demo_data() -> None:
    now = datetime.now(UTC)
    with SessionLocal() as db:
        db.add(models.Department(id=DEMO_ID, code="LOCK", name="Concurrency Proof"))
        db.flush()

        db.add(models.Major(id=DEMO_ID, department_id=DEMO_ID, code="LOCK", name="Locking Demo"))
        db.add(models.Semester(id=DEMO_ID, name="Concurrency Proof", status="active"))
        db.flush()

        db.add(
            models.Course(
                id=DEMO_ID,
                department_id=DEMO_ID,
                code="LOCK101",
                title="Concurrency Proof",
                credits=3,
            )
        )
        db.flush()

        db.add(
            models.CourseOffering(
                id=DEMO_ID, course_id=DEMO_ID, semester_id=DEMO_ID, status="active"
            )
        )
        db.flush()

        db.add(
            models.Section(
                id=DEMO_ID,
                course_offering_id=DEMO_ID,
                section_code="001",
                capacity=1,
                status="open",
            )
        )
        db.flush()

        db.add(
            models.RegistrationPeriod(
                id=DEMO_ID,
                semester_id=DEMO_ID,
                opens_at=now - timedelta(hours=1),
                closes_at=now + timedelta(hours=1),
                status="open",
            )
        )
        db.add(
            models.SectionSchedule(
                id=DEMO_ID,
                section_id=DEMO_ID,
                day_of_week="Monday",
                start_time="09:00",
                end_time="10:00",
            )
        )

        for student_id in STUDENT_IDS:
            db.add(
                models.Student(
                    id=student_id,
                    student_number=f"LOCK{student_id}",
                    full_name=f"Concurrency Student {student_id}",
                    profile_source="manual",
                )
            )

        db.flush()

        for student_id in STUDENT_IDS:
            db.add(
                models.StudentAcademicProfile(
                    student_id=student_id,
                    department_id=DEMO_ID,
                    major_id=DEMO_ID,
                    academic_year=3,
                    gpa_is_verified=False,
                )
            )
        db.commit()


if __name__ == "__main__":
    raise SystemExit(main())
