from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ProfessorRoomPreference, Room, RoomAllocation, Section, SectionSchedule
from app.modules.rooms.schemas import RoomCreate


class RoomRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_room(self, data: RoomCreate) -> Room:
        room = Room(
            building=data.building,
            room_number=data.room_number,
            capacity=data.capacity,
            room_type=data.room_type,
            is_active=True,
        )
        self.db.add(room)
        self.db.flush()
        return room

    def get_room(self, room_id: int) -> Room | None:
        return self.db.get(Room, room_id)

    def get_room_by_location(self, building: str | None, room_number: str) -> Room | None:
        stmt = select(Room).where(
            Room.building == building,
            Room.room_number == room_number,
        )
        return self.db.scalars(stmt).one_or_none()

    def list_rooms(self, active_only: bool = True) -> Sequence[Room]:
        stmt = select(Room)
        if active_only:
            stmt = stmt.where(Room.is_active.is_(True))
        stmt = stmt.order_by(Room.building, Room.room_number)
        return self.db.scalars(stmt).all()

    def create_allocation(
        self, section_id: int, room_id: int, user_id: int | None, is_preferred: bool = False
    ) -> RoomAllocation:
        alloc = RoomAllocation(
            section_id=section_id,
            room_id=room_id,
            allocated_by_user_id=user_id,
            is_preferred=is_preferred,
        )
        self.db.add(alloc)
        self.db.flush()
        return alloc

    def get_allocation(self, section_id: int, room_id: int) -> RoomAllocation | None:
        stmt = select(RoomAllocation).where(
            RoomAllocation.section_id == section_id,
            RoomAllocation.room_id == room_id,
        )
        return self.db.scalars(stmt).one_or_none()

    def list_allocations(self, section_id: int) -> Sequence[RoomAllocation]:
        stmt = (
            select(RoomAllocation)
            .where(RoomAllocation.section_id == section_id)
            .order_by(RoomAllocation.id)
        )
        return self.db.scalars(stmt).all()

    def get_sections_using_room_at_slots(
        self, room_id: int, slots: list[tuple[str, str, str]]
    ) -> Sequence[Section]:
        """Return sections that have booked this room and overlap with any of the given slots."""
        if not slots:
            return []

        pref_ids = set(
            self.db.scalars(
                select(ProfessorRoomPreference.section_id).where(
                    ProfessorRoomPreference.room_id == room_id,
                    ProfessorRoomPreference.status == "selected",
                )
            ).all()
        )
        alloc_ids = set(
            self.db.scalars(
                select(RoomAllocation.section_id).where(
                    RoomAllocation.room_id == room_id,
                    RoomAllocation.is_preferred.is_(True),
                )
            ).all()
        )
        booked_ids = pref_ids | alloc_ids
        if not booked_ids:
            return []

        conflicting_ids: set[int] = set()
        for day, start, end in slots:
            stmt = select(SectionSchedule.section_id).where(
                SectionSchedule.section_id.in_(booked_ids),
                SectionSchedule.day_of_week == day,
                SectionSchedule.start_time < end,
                SectionSchedule.end_time > start,
            )
            conflicting_ids.update(self.db.scalars(stmt).all())

        if not conflicting_ids:
            return []
        return self.db.scalars(select(Section).where(Section.id.in_(conflicting_ids))).all()

    def get_room_for_section(self, section_id: int) -> Room | None:
        """Canonical helper: returns the confirmed room for a section.
        Priority: professor_room_preferences (status=selected) > room_allocations (is_preferred).
        """
        pref_stmt = (
            select(Room)
            .join(
                ProfessorRoomPreference,
                ProfessorRoomPreference.room_id == Room.id,
            )
            .where(
                ProfessorRoomPreference.section_id == section_id,
                ProfessorRoomPreference.status == "selected",
            )
            .limit(1)
        )
        room = self.db.scalars(pref_stmt).first()
        if room:
            return room

        alloc_stmt = (
            select(Room)
            .join(RoomAllocation, RoomAllocation.room_id == Room.id)
            .where(
                RoomAllocation.section_id == section_id,
                RoomAllocation.is_preferred.is_(True),
            )
            .limit(1)
        )
        return self.db.scalars(alloc_stmt).first()
