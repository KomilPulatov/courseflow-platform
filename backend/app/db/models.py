from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'professor', 'student')", name="ck_user_role"),
    )


class Professor(Base):
    __tablename__ = "professors"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_name: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    sections: Mapped[list["Section"]] = relationship("Section", viewonly=True)


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True)
    student_number: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_source: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    academic_profile: Mapped["StudentAcademicProfile | None"] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
        uselist=False,
    )
    completed_courses: Mapped[list["StudentCompletedCourse"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("profile_source IN ('ins_verified', 'manual')", name="ck_student_source"),
    )


class StudentAcademicProfile(Base):
    __tablename__ = "student_academic_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), unique=True, nullable=False)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    major_id: Mapped[int | None] = mapped_column(ForeignKey("majors.id"))
    department_name: Mapped[str | None] = mapped_column(String(255))
    major_name: Mapped[str | None] = mapped_column(String(255))
    academic_year: Mapped[int | None] = mapped_column(Integer)
    group_name: Mapped[str | None] = mapped_column(String(80))
    current_gpa: Mapped[float | None] = mapped_column(Numeric(3, 2))
    gpa_is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    academic_status: Mapped[str | None] = mapped_column(String(40))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    student: Mapped[Student] = relationship(back_populates="academic_profile")

    __table_args__ = (
        CheckConstraint(
            "academic_year IS NULL OR academic_year BETWEEN 1 AND 6",
            name="ck_profile_academic_year",
        ),
    )


class StudentCompletedCourse(Base):
    __tablename__ = "student_completed_courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"))
    course_code: Mapped[str] = mapped_column(String(40), nullable=False)
    course_title: Mapped[str | None] = mapped_column(String(255))
    grade: Mapped[str | None] = mapped_column(String(10))
    credits: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    completed_semester: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    student: Mapped[Student] = relationship(back_populates="completed_courses")

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "course_code",
            "course_title",
            name="uq_completed_student_course_identity",
        ),
        CheckConstraint("source IN ('ins_verified', 'manual')", name="ck_completed_source"),
    )


class ExternalAccount(Base):
    __tablename__ = "external_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    external_user_id: Mapped[str | None] = mapped_column(String(120))
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("provider", "external_user_id", name="uq_external_provider_user"),
    )


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Major(Base):
    __tablename__ = "majors"

    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("department_id", "code", name="uq_major_department_code"),
        UniqueConstraint("department_id", "name", name="uq_major_department_name"),
    )


class AcademicProgram(Base):
    __tablename__ = "academic_programs"

    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    degree_level: Mapped[str] = mapped_column(String(30), nullable=False, default="undergraduate")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("department_id", "name", name="uq_program_department_name"),
        CheckConstraint(
            "degree_level IN ('undergraduate', 'graduate')",
            name="ck_academic_program_degree_level",
        ),
    )


class Semester(Base):
    __tablename__ = "semesters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("name", name="uq_semester_name"),
        CheckConstraint(
            "status IN ('draft', 'active', 'archived')",
            name="ck_semester_status",
        ),
    )


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    course_type: Mapped[str | None] = mapped_column(String(40))
    is_repeatable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("code", "title", "credits", name="uq_course_catalog_identity"),
        CheckConstraint("credits > 0", name="ck_course_credits_positive"),
    )


class CoursePrerequisite(Base):
    __tablename__ = "course_prerequisites"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    prerequisite_course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    rule_group: Mapped[str] = mapped_column(String(40), nullable=False, default="all")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint(
            "course_id",
            "prerequisite_course_id",
            name="uq_course_prerequisite",
        ),
        CheckConstraint("course_id <> prerequisite_course_id", name="ck_course_not_own_prereq"),
    )


class CourseEligibilityRule(Base):
    __tablename__ = "course_eligibility_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    min_academic_year: Mapped[int | None] = mapped_column(Integer)
    min_gpa: Mapped[float | None] = mapped_column(Numeric(3, 2))
    allowed_department_ids: Mapped[list[int] | None] = mapped_column(JSON)
    allowed_major_ids: Mapped[list[int] | None] = mapped_column(JSON)
    rule_metadata: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CurriculumCourse(Base):
    __tablename__ = "curriculum_courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("academic_programs.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("program_id", "course_id", name="uq_curriculum_program_course"),
    )


class CurriculumCoursePlacement(Base):
    __tablename__ = "curriculum_course_placements"

    id: Mapped[int] = mapped_column(primary_key=True)
    curriculum_course_id: Mapped[int] = mapped_column(
        ForeignKey("curriculum_courses.id"),
        nullable=False,
    )
    academic_year: Mapped[int] = mapped_column(Integer, nullable=False)
    term: Mapped[str] = mapped_column(String(10), nullable=False)
    slot_type: Mapped[str] = mapped_column(String(20), nullable=False, default="primary")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint(
            "curriculum_course_id",
            "academic_year",
            "term",
            name="uq_curriculum_course_term",
        ),
        CheckConstraint("academic_year BETWEEN 1 AND 4", name="ck_curriculum_placement_year"),
        CheckConstraint("term IN ('fall', 'spring')", name="ck_curriculum_placement_term"),
        CheckConstraint(
            "slot_type IN ('primary', 'optional')",
            name="ck_curriculum_placement_slot_type",
        ),
    )


class CourseOffering(Base):
    __tablename__ = "course_offerings"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    course: Mapped["Course"] = relationship("Course")
    semester: Mapped["Semester"] = relationship("Semester")

    __table_args__ = (
        UniqueConstraint("course_id", "semester_id", name="uq_course_offering_course_semester"),
        CheckConstraint(
            "status IN ('draft', 'active', 'cancelled', 'archived')",
            name="ck_course_offering_status",
        ),
    )


class Section(Base):
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_offering_id: Mapped[int] = mapped_column(
        ForeignKey("course_offerings.id"),
        nullable=False,
    )
    professor_id: Mapped[int | None] = mapped_column(ForeignKey("professors.id"))
    section_code: Mapped[str] = mapped_column(String(40), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    room_selection_mode: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="admin_fixed",
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    offering: Mapped[CourseOffering] = relationship()
    schedules: Mapped[list["SectionSchedule"]] = relationship("SectionSchedule")
    room_allocations: Mapped[list["RoomAllocation"]] = relationship("RoomAllocation")
    room_preferences: Mapped[list["ProfessorRoomPreference"]] = relationship(
        "ProfessorRoomPreference",
    )

    __table_args__ = (
        UniqueConstraint("course_offering_id", "section_code", name="uq_section_offering_code"),
        CheckConstraint("capacity > 0", name="ck_section_capacity_positive"),
        CheckConstraint(
            "room_selection_mode IN ('admin_fixed', 'professor_choice', 'system_recommended')",
            name="ck_section_room_selection_mode",
        ),
        CheckConstraint(
            "status IN ('draft', 'open', 'closed', 'cancelled')",
            name="ck_section_status",
        ),
    )


class SectionSchedule(Base):
    __tablename__ = "section_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"), nullable=False)
    day_of_week: Mapped[str] = mapped_column(String(12), nullable=False)
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    building: Mapped[str | None] = mapped_column(String(80))
    room_number: Mapped[str] = mapped_column(String(40), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    room_type: Mapped[str] = mapped_column(String(40), nullable=False, default="lecture")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("capacity > 0", name="ck_room_capacity"),
        UniqueConstraint("building", "room_number", name="uq_room_location"),
    )


class RoomAllocation(Base):
    __tablename__ = "room_allocations"

    id: Mapped[int] = mapped_column(primary_key=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    allocated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    is_preferred: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    room: Mapped[Room] = relationship()

    __table_args__ = (
        UniqueConstraint("section_id", "room_id", name="uq_room_alloc"),
    )


class ProfessorRoomPreference(Base):
    __tablename__ = "professor_room_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"), nullable=False)
    professor_id: Mapped[int] = mapped_column(ForeignKey("professors.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    preference_rank: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="selected")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    room: Mapped[Room] = relationship()

    __table_args__ = (
        UniqueConstraint("section_id", "professor_id", name="uq_prof_pref_section_professor"),
    )


class TimetableSuggestionRun(Base):
    __tablename__ = "timetable_suggestion_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False)
    strategy: Mapped[str] = mapped_column(
        String(60), nullable=False, default="balanced_heuristic"
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="completed")
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    items: Mapped[list["TimetableSuggestionItem"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class TimetableSuggestionItem(Base):
    __tablename__ = "timetable_suggestion_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("timetable_suggestion_runs.id"), nullable=False
    )
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"), nullable=False)
    suggested_room_id: Mapped[int | None] = mapped_column(ForeignKey("rooms.id"))
    score: Mapped[float | None] = mapped_column(Numeric(6, 3))
    breakdown: Mapped[dict | None] = mapped_column(JSON)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    run: Mapped[TimetableSuggestionRun] = relationship(back_populates="items")
    suggested_room: Mapped[Room | None] = relationship()
    section: Mapped["Section"] = relationship()


class RegistrationPeriod(Base):
    __tablename__ = "registration_periods"

    id: Mapped[int] = mapped_column(primary_key=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False)
    opens_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closes_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="enrolled")
    idempotency_key: Mapped[str | None] = mapped_column(String(120))
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    dropped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    section: Mapped[Section] = relationship()
    course: Mapped[Course] = relationship()
    semester: Mapped[Semester] = relationship()

    __table_args__ = (
        UniqueConstraint("student_id", "section_id", name="uq_enrollment_student_section"),
        UniqueConstraint(
            "student_id",
            "course_id",
            "semester_id",
            name="uq_enrollment_student_course_semester",
        ),
    )


class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="waiting")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("student_id", "section_id", name="uq_waitlist_student_section"),
        UniqueConstraint("section_id", "position", name="uq_waitlist_section_position"),
    )


class RegistrationIdempotencyKey(Base):
    __tablename__ = "registration_idempotency_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_body: Mapped[dict] = mapped_column(JSON, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("student_id", "idempotency_key", name="uq_registration_idempotency"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"))
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer)
    payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class RegistrationEvent(Base):
    __tablename__ = "registration_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"))
    section_id: Mapped[int | None] = mapped_column(ForeignKey("sections.id"))
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
