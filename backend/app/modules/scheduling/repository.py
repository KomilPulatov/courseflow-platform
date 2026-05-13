from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    CourseOffering,
    Room,
    Section,
    Semester,
    TimetableSuggestionItem,
    TimetableSuggestionRun,
)


class SchedulingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_open_sections_for_semester(self, semester_id: int) -> Sequence[Section]:
        stmt = (
            select(Section)
            .join(CourseOffering, CourseOffering.id == Section.course_offering_id)
            .options(
                joinedload(Section.schedules),
                joinedload(Section.offering).joinedload(CourseOffering.course),
                joinedload(Section.offering).joinedload(CourseOffering.semester),
                joinedload(Section.room_allocations),
                joinedload(Section.room_preferences),
            )
            .where(
                CourseOffering.semester_id == semester_id,
                Section.status.in_(["open", "draft"]),
            )
            .order_by(Section.id)
        )
        return self.db.scalars(stmt).unique().all()

    def list_active_rooms(self) -> Sequence[Room]:
        stmt = (
            select(Room).where(Room.is_active.is_(True)).order_by(Room.building, Room.room_number)
        )
        return self.db.scalars(stmt).all()

    def get_semester(self, semester_id: int) -> Semester | None:
        return self.db.get(Semester, semester_id)

    def create_run(
        self,
        semester_id: int,
        strategy: str,
        created_by_user_id: int | None,
    ) -> TimetableSuggestionRun:
        run = TimetableSuggestionRun(
            semester_id=semester_id,
            strategy=strategy,
            status="running",
            created_by_user_id=created_by_user_id,
        )
        self.db.add(run)
        self.db.flush()
        return run

    def create_item(
        self,
        run_id: int,
        section_id: int,
        suggested_room_id: int | None,
        score: float | None,
        breakdown: dict | None,
    ) -> TimetableSuggestionItem:
        item = TimetableSuggestionItem(
            run_id=run_id,
            section_id=section_id,
            suggested_room_id=suggested_room_id,
            score=score,
            breakdown=breakdown,
            approved=False,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def get_run(self, run_id: int) -> TimetableSuggestionRun | None:
        stmt = (
            select(TimetableSuggestionRun)
            .options(
                joinedload(TimetableSuggestionRun.items)
                .joinedload(TimetableSuggestionItem.suggested_room),
                joinedload(TimetableSuggestionRun.items)
                .joinedload(TimetableSuggestionItem.section)
                .joinedload(Section.offering)
                .joinedload(CourseOffering.course),
            )
            .where(TimetableSuggestionRun.id == run_id)
        )
        return self.db.scalars(stmt).unique().one_or_none()

    def list_items_for_run(self, run_id: int) -> Sequence[TimetableSuggestionItem]:
        stmt = (
            select(TimetableSuggestionItem)
            .options(
                joinedload(TimetableSuggestionItem.suggested_room),
                joinedload(TimetableSuggestionItem.section)
                .joinedload(Section.offering)
                .joinedload(CourseOffering.course),
            )
            .where(TimetableSuggestionItem.run_id == run_id)
            .order_by(TimetableSuggestionItem.id)
        )
        return self.db.scalars(stmt).unique().all()
