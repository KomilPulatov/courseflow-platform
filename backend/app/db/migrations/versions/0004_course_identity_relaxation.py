"""relax course code uniqueness for cross-program conflicts

Revision ID: 0004_course_identity_relaxation
Revises: 0003_curriculum_relations
Create Date: 2026-05-11 10:30:00
"""

from alembic import op

revision = "0004_course_identity_relaxation"
down_revision = "0003_curriculum_relations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("courses") as batch_op:
        batch_op.drop_constraint("uq_course_code", type_="unique")
        batch_op.create_unique_constraint(
            "uq_course_catalog_identity",
            ["code", "title", "credits"],
        )

    with op.batch_alter_table("student_completed_courses") as batch_op:
        batch_op.drop_constraint("uq_completed_student_course_code", type_="unique")
        batch_op.create_unique_constraint(
            "uq_completed_student_course_identity",
            ["student_id", "course_code", "course_title"],
        )


def downgrade() -> None:
    with op.batch_alter_table("student_completed_courses") as batch_op:
        batch_op.drop_constraint("uq_completed_student_course_identity", type_="unique")
        batch_op.create_unique_constraint(
            "uq_completed_student_course_code",
            ["student_id", "course_code"],
        )

    with op.batch_alter_table("courses") as batch_op:
        batch_op.drop_constraint("uq_course_catalog_identity", type_="unique")
        batch_op.create_unique_constraint("code", ["code"])
