"""add rooms scheduling and notifications

Revision ID: 0005_rooms_scheduling_platform
Revises: 0004_course_identity_relaxation
Create Date: 2026-05-12 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_rooms_scheduling_platform"
down_revision: str | None = "0004_course_identity_relaxation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("building", sa.String(length=80), nullable=True),
        sa.Column("room_number", sa.String(length=40), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("room_type", sa.String(length=40), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("capacity > 0", name="ck_room_capacity_positive"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("building", "room_number", name="uq_room_building_number"),
    )
    op.create_table(
        "time_slots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.String(length=12), nullable=False),
        sa.Column("start_time", sa.String(length=5), nullable=False),
        sa.Column("end_time", sa.String(length=5), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("day_of_week", "start_time", "end_time", name="uq_time_slot_window"),
    )
    op.create_table(
        "room_allocations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("allocated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_preferred", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["allocated_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("section_id", "room_id", name="uq_room_allocation_section_room"),
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
        sa.CheckConstraint("preference_rank > 0", name="ck_prof_room_preference_rank_positive"),
        sa.CheckConstraint(
            "status IN ('selected', 'cancelled')",
            name="ck_prof_room_preference_status",
        ),
        sa.ForeignKeyConstraint(["professor_id"], ["professors.id"]),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "section_id",
            "professor_id",
            "room_id",
            name="uq_professor_room_preference",
        ),
    )
    op.create_table(
        "timetable_suggestion_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("semester_id", sa.Integer(), nullable=False),
        sa.Column("strategy", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'completed', 'approved', 'failed')",
            name="ck_timetable_run_status",
        ),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["semester_id"], ["semesters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "timetable_suggestion_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=True),
        sa.Column("time_slot_id", sa.Integer(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('suggested', 'approved', 'rejected')",
            name="ck_timetable_item_status",
        ),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["timetable_suggestion_runs.id"]),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"]),
        sa.ForeignKeyConstraint(["time_slot_id"], ["time_slots.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "section_id", name="uq_timetable_item_run_section"),
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("student_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('unread', 'read', 'archived')",
            name="ck_notification_status",
        ),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("section_schedules") as batch_op:
        batch_op.add_column(sa.Column("room_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("time_slot_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_section_schedules_room_id", "rooms", ["room_id"], ["id"])
        batch_op.create_foreign_key(
            "fk_section_schedules_time_slot_id",
            "time_slots",
            ["time_slot_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("section_schedules") as batch_op:
        batch_op.drop_constraint("fk_section_schedules_time_slot_id", type_="foreignkey")
        batch_op.drop_constraint("fk_section_schedules_room_id", type_="foreignkey")
        batch_op.drop_column("time_slot_id")
        batch_op.drop_column("room_id")
    op.drop_table("notifications")
    op.drop_table("timetable_suggestion_items")
    op.drop_table("timetable_suggestion_runs")
    op.drop_table("professor_room_preferences")
    op.drop_table("room_allocations")
    op.drop_table("time_slots")
    op.drop_table("rooms")
