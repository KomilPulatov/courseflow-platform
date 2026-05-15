"""curriculum relations for shared course catalog

Revision ID: 0003_curriculum_relations
Revises: 0002_academic_foundation
Create Date: 2026-05-11 10:00:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0003_curriculum_relations"
down_revision = "0002_academic_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "academic_programs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("degree_level", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "degree_level IN ('undergraduate', 'graduate')",
            name="ck_academic_program_degree_level",
        ),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("department_id", "name", name="uq_program_department_name"),
    )
    op.create_table(
        "curriculum_courses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("program_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.ForeignKeyConstraint(["program_id"], ["academic_programs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("program_id", "course_id", name="uq_curriculum_program_course"),
    )
    op.create_table(
        "curriculum_course_placements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("curriculum_course_id", sa.Integer(), nullable=False),
        sa.Column("academic_year", sa.Integer(), nullable=False),
        sa.Column("term", sa.String(length=10), nullable=False),
        sa.Column("slot_type", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("academic_year BETWEEN 1 AND 4", name="ck_curriculum_placement_year"),
        sa.CheckConstraint("term IN ('fall', 'spring')", name="ck_curriculum_placement_term"),
        sa.CheckConstraint(
            "slot_type IN ('primary', 'optional')",
            name="ck_curriculum_placement_slot_type",
        ),
        sa.ForeignKeyConstraint(["curriculum_course_id"], ["curriculum_courses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "curriculum_course_id",
            "academic_year",
            "term",
            name="uq_curriculum_course_term",
        ),
    )


def downgrade() -> None:
    op.drop_table("curriculum_course_placements")
    op.drop_table("curriculum_courses")
    op.drop_table("academic_programs")
