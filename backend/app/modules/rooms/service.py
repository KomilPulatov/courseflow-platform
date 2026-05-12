from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Section
from app.modules.rooms.repository import RoomRepository
from app.modules.rooms.schemas import (
    RoomAllocationCreate,
    RoomAllocationRead,
    RoomCreate,
    RoomOptionRead,
    RoomRead,
)


class RoomService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RoomRepository(db)

    def create_room(self, data: RoomCreate) -> RoomRead:
        existing = self.repo.get_room_by_location(data.building, data.room_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Room {data.building}-{data.room_number} already exists.",
            )
        room = self.repo.create_room(data)
        self.db.commit()
        return RoomRead.model_validate(room)

    def list_rooms(self) -> list[RoomRead]:
        return [RoomRead.model_validate(r) for r in self.repo.list_rooms()]

    def allocate_rooms_to_section(
        self,
        section_id: int,
        data: RoomAllocationCreate,
        admin_user_id: int,
    ) -> list[RoomAllocationRead]:
        section = self.db.get(Section, section_id)
        if not section:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found.")

        results = []
        for room_id in data.room_ids:
            room = self.repo.get_room(room_id)
            if not room:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Room {room_id} not found.",
                )
            existing = self.repo.get_allocation(section_id, room_id)
            if existing:
                results.append(existing)
                continue
            alloc = self.repo.create_allocation(
                section_id=section_id,
                room_id=room_id,
                user_id=admin_user_id,
            )
            results.append(alloc)

        self.db.commit()
        return [RoomAllocationRead.model_validate(a) for a in results]

    def list_allocations(self, section_id: int) -> list[RoomAllocationRead]:
        section = self.db.get(Section, section_id)
        if not section:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found.")
        allocs = self.repo.list_allocations(section_id)
        return [RoomAllocationRead.model_validate(a) for a in allocs]

    def list_section_room_options(self, section_id: int) -> list[RoomOptionRead]:
        allocs = self.repo.list_allocations(section_id)
        section = self.db.get(Section, section_id)
        if not section:
            return []

        section_slots = [
            (s.day_of_week, s.start_time, s.end_time) for s in section.schedules
        ]

        options = []
        for alloc in allocs:
            room = alloc.room
            conflicts = self.repo.get_sections_using_room_at_slots(room.id, section_slots)
            conflicting_ids = {s.id for s in conflicts}
            available = section_id not in conflicting_ids
            options.append(
                RoomOptionRead(
                    room_id=room.id,
                    building=room.building,
                    room_number=room.room_number,
                    capacity=room.capacity,
                    room_type=room.room_type,
                    available=available,
                )
            )
        return options
