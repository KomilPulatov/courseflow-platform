from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    CourseOffering,
    Professor,
    ProfessorRoomPreference,
    Section,
    SectionSchedule,
)


class ProfessorRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_professor_by_user_id(self, user_id: int) -> Professor | None:
        stmt = select(Professor).where(Professor.user_id == user_id)
        return self.db.scalars(stmt).one_or_none()

    def list_professors(self) -> Sequence[Professor]:
        return self.db.scalars(select(Professor).order_by(Professor.full_name)).all()

    def list_sections_by_professor(self, professor_id: int) -> Sequence[Section]:
        stmt = (
            select(Section)
            .options(
                joinedload(Section.schedules),
                joinedload(Section.offering).joinedload(CourseOffering.course),
                joinedload(Section.offering).joinedload(CourseOffering.semester),
            )
            .where(Section.professor_id == professor_id)
            .order_by(Section.id)
        )
        return self.db.scalars(stmt).unique().all()

    def get_section_for_professor(self, section_id: int, professor_id: int) -> Section | None:
        stmt = (
            select(Section)
            .options(joinedload(Section.schedules))
            .where(
                Section.id == section_id,
                Section.professor_id == professor_id,
            )
        )
        return self.db.scalars(stmt).unique().one_or_none()

    def get_existing_preference(
        self, section_id: int, professor_id: int
    ) -> ProfessorRoomPreference | None:
        stmt = select(ProfessorRoomPreference).where(
            ProfessorRoomPreference.section_id == section_id,
            ProfessorRoomPreference.professor_id == professor_id,
        )
        return self.db.scalars(stmt).one_or_none()

    def save_preference(
        self,
        section_id: int,
        professor_id: int,
        room_id: int,
        rank: int,
    ) -> ProfessorRoomPreference:
        existing = self.get_existing_preference(section_id, professor_id)
        if existing:
            existing.room_id = room_id
            existing.preference_rank = rank
            existing.status = "selected"
            self.db.flush()
            return existing
        pref = ProfessorRoomPreference(
            section_id=section_id,
            professor_id=professor_id,
            room_id=room_id,
            preference_rank=rank,
            status="selected",
        )
        self.db.add(pref)
        self.db.flush()
        return pref

    def get_sections_by_professor_at_slots(
        self, professor_id: int, slots: list[tuple[str, str, str]], exclude_section_id: int
    ) -> Sequence[Section]:
        if not slots:
            return []
        conflicting_ids: set[int] = set()
        for day, start, end in slots:
            stmt = (
                select(SectionSchedule.section_id)
                .join(Section, Section.id == SectionSchedule.section_id)
                .where(
                    Section.professor_id == professor_id,
                    Section.id != exclude_section_id,
                    SectionSchedule.day_of_week == day,
                    SectionSchedule.start_time < end,
                    SectionSchedule.end_time > start,
                )
            )
            conflicting_ids.update(self.db.scalars(stmt).all())
        if not conflicting_ids:
            return []
        return self.db.scalars(select(Section).where(Section.id.in_(conflicting_ids))).all()
