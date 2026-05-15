"""academic foundation for catalog and offerings

Revision ID: 0002_academic_foundation
Revises: 0001_registration_slice
Create Date: 2026-05-10 16:00:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_academic_foundation"
down_revision = "0001_registration_slice"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "majors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("department_id", "code", name="uq_major_department_code"),
        sa.UniqueConstraint("department_id", "name", name="uq_major_department_name"),
    )

    with op.batch_alter_table("student_academic_profiles") as batch_op:
        batch_op.create_foreign_key(
            "fk_profile_department_id",
            "departments",
            ["department_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_profile_major_id",
            "majors",
            ["major_id"],
            ["id"],
        )

    with op.batch_alter_table("semesters") as batch_op:
        batch_op.create_unique_constraint("uq_semester_name", ["name"])
        batch_op.create_check_constraint(
            "ck_semester_status",
            "status IN ('draft', 'active', 'archived')",
        )

    with op.batch_alter_table("courses") as batch_op:
        batch_op.create_foreign_key(
            "fk_courses_department_id",
            "departments",
            ["department_id"],
            ["id"],
        )

    with op.batch_alter_table("course_prerequisites") as batch_op:
        batch_op.create_check_constraint(
            "ck_course_not_own_prereq",
            "course_id <> prerequisite_course_id",
        )

    with op.batch_alter_table("course_offerings") as batch_op:
        batch_op.create_unique_constraint(
            "uq_course_offering_course_semester",
            ["course_id", "semester_id"],
        )
        batch_op.create_check_constraint(
            "ck_course_offering_status",
            "status IN ('draft', 'active', 'cancelled', 'archived')",
        )

    with op.batch_alter_table("sections") as batch_op:
        batch_op.create_foreign_key(
            "fk_sections_professor_id",
            "professors",
            ["professor_id"],
            ["id"],
        )
        batch_op.create_check_constraint(
            "ck_section_room_selection_mode",
            "room_selection_mode IN ('admin_fixed', 'professor_choice', 'system_recommended')",
        )
        batch_op.create_check_constraint(
            "ck_section_status",
            "status IN ('draft', 'open', 'closed', 'cancelled')",
        )


def downgrade() -> None:
    with op.batch_alter_table("sections") as batch_op:
        batch_op.drop_constraint("ck_section_status", type_="check")
        batch_op.drop_constraint("ck_section_room_selection_mode", type_="check")
        batch_op.drop_constraint("fk_sections_professor_id", type_="foreignkey")

    with op.batch_alter_table("course_offerings") as batch_op:
        batch_op.drop_constraint("ck_course_offering_status", type_="check")
        batch_op.drop_constraint("uq_course_offering_course_semester", type_="unique")

    with op.batch_alter_table("course_prerequisites") as batch_op:
        batch_op.drop_constraint("ck_course_not_own_prereq", type_="check")

    with op.batch_alter_table("courses") as batch_op:
        batch_op.drop_constraint("fk_courses_department_id", type_="foreignkey")

    with op.batch_alter_table("semesters") as batch_op:
        batch_op.drop_constraint("ck_semester_status", type_="check")
        batch_op.drop_constraint("uq_semester_name", type_="unique")

    with op.batch_alter_table("student_academic_profiles") as batch_op:
        batch_op.drop_constraint("fk_profile_major_id", type_="foreignkey")
        batch_op.drop_constraint("fk_profile_department_id", type_="foreignkey")

    op.drop_table("majors")
    op.drop_table("departments")
