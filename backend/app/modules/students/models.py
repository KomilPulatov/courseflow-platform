from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), unique=True, nullable=True
    )
    student_number: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_source: Mapped[str] = mapped_column(String(30), nullable=False)  # ins_verified | manual
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class StudentAcademicProfile(Base):
    __tablename__ = "student_academic_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id"), unique=True, nullable=False
    )
    # FK to departments/majors (nullable — may not exist yet for INS students)
    department_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("departments.id"), nullable=True
    )
    major_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("majors.id"), nullable=True)
    # Store names directly from INS so we don't need FK match immediately
    department_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    major_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    academic_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_gpa: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    # KEY FIELD: True only for INS-verified students — drives GPA eligibility rule
    gpa_is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    academic_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class StudentCompletedCourse(Base):
    __tablename__ = "student_completed_courses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("students.id"), nullable=False)
    course_code: Mapped[str] = mapped_column(String(40), nullable=False)
    course_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    credits: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False)  # ins_verified | manual

    __table_args__ = (UniqueConstraint("student_id", "course_code", name="uq_student_course"),)


class ExternalAccount(Base):
    __tablename__ = "external_accounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("students.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, server_default="ins")
    external_user_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(nullable=True)

    __table_args__ = (UniqueConstraint("provider", "external_user_id", name="uq_external_account"),)
