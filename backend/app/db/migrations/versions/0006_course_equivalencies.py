"""add course equivalencies

Revision ID: 0006_course_equivalencies
Revises: 0005_rooms_scheduling_platform
Create Date: 2026-05-17 01:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_course_equivalencies"
down_revision: str | None = "0005_rooms_scheduling_platform"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "course_equivalencies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("equivalent_course_id", sa.Integer(), nullable=False),
        sa.Column("equivalence_type", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "course_id <> equivalent_course_id",
            name="ck_course_not_own_equivalent",
        ),
        sa.CheckConstraint("course_id < equivalent_course_id", name="ck_course_equivalency_order"),
        sa.CheckConstraint(
            "equivalence_type IN ('cross_program', 'substitution')",
            name="ck_course_equivalency_type",
        ),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.ForeignKeyConstraint(["equivalent_course_id"], ["courses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "equivalent_course_id", name="uq_course_equivalency_pair"),
    )


def downgrade() -> None:
    op.drop_table("course_equivalencies")
