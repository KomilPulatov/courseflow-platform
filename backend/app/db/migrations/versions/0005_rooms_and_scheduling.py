"""rooms and scheduling tables

Revision ID: 0005_rooms_and_scheduling
Revises: 0004_course_identity_relaxation
Create Date: 2026-05-12 00:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "0005_rooms_and_scheduling"
down_revision = "0004_course_identity_relaxation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("building", sa.String(length=80), nullable=True),
        sa.Column("room_number", sa.String(length=40), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("room_type", sa.String(length=40), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.CheckConstraint("capacity > 0", name="ck_room_capacity"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("building", "room_number", name="uq_room_location"),
    )
    op.create_table(
        "room_allocations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("allocated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("is_preferred", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["allocated_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("section_id", "room_id", name="uq_room_alloc"),
    )
    op.create_table(
        "professor_room_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=False),
        sa.Column("professor_id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("preference_rank", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["professor_id"], ["professors.id"]),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("section_id", "professor_id", name="uq_prof_pref_section_professor"),
    )
    op.create_table(
        "timetable_suggestion_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("semester_id", sa.Integer(), nullable=False),
        sa.Column("strategy", sa.String(length=60), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["semester_id"], ["semesters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "timetable_suggestion_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=False),
        sa.Column("suggested_room_id", sa.Integer(), nullable=True),
        sa.Column("score", sa.Numeric(precision=6, scale=3), nullable=True),
        sa.Column("breakdown", sa.JSON(), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["timetable_suggestion_runs.id"]),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"]),
        sa.ForeignKeyConstraint(["suggested_room_id"], ["rooms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_room_allocations_section", "room_allocations", ["section_id"])
    op.create_index("idx_prof_room_pref_section", "professor_room_preferences", ["section_id"])
    op.create_index("idx_suggestion_runs_semester", "timetable_suggestion_runs", ["semester_id"])


def downgrade() -> None:
    op.drop_index("idx_suggestion_runs_semester", table_name="timetable_suggestion_runs")
    op.drop_index("idx_prof_room_pref_section", table_name="professor_room_preferences")
    op.drop_index("idx_room_allocations_section", table_name="room_allocations")
    op.drop_table("timetable_suggestion_items")
    op.drop_table("timetable_suggestion_runs")
    op.drop_table("professor_room_preferences")
    op.drop_table("room_allocations")
    op.drop_table("rooms")
