from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db import models
from app.modules.rooms import schemas


class RoomService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_professor(self, payload: schemas.ProfessorCreate) -> schemas.ProfessorRead:
        existing_user = self.db.execute(
            select(models.User).where(func.lower(models.User.email) == payload.email.lower())
        ).scalar_one_or_none()
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )

        user = models.User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            role="professor",
        )
        self.db.add(user)
        self.db.flush()
        professor = models.Professor(
            user_id=user.id,
            full_name=payload.full_name,
            department_name=payload.department_name,
        )
        self.db.add(professor)
        self.db.commit()
        return self._professor_read(professor, user)

    def list_professors(self) -> list[schemas.ProfessorRead]:
        professors = list(self.db.execute(select(models.Professor)).scalars())
        return [self._professor_read(p) for p in professors]

    def create_room(self, payload: schemas.RoomCreate) -> schemas.RoomRead:
        existing = self.db.execute(
            select(models.Room).where(
                models.Room.building == payload.building,
                func.lower(models.Room.room_number) == payload.room_number.lower(),
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Room already exists.",
            )
        room = models.Room(**payload.model_dump())
        self.db.add(room)
        self.db.commit()
        return self._room_read(room)

    def list_rooms(self) -> list[schemas.RoomRead]:
        rooms = list(self.db.execute(select(models.Room)).scalars())
        return [self._room_read(r) for r in rooms]

    def allocate_rooms(
        self,
        *,
        section_id: int,
        payload: schemas.RoomAllocationCreate,
        allocated_by_user_id: int,
    ) -> list[schemas.RoomAllocationRead]:
        section = self._get_section(section_id)
        rows: list[models.RoomAllocation] = []
        for room_id in payload.room_ids:
            room = self.db.get(models.Room, room_id)
            if room is None or not room.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Room {room_id} was not found or is inactive.",
                )
            if room.capacity < section.capacity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Room {room_id} capacity is below section capacity.",
                )
            existing = self.db.execute(
                select(models.RoomAllocation).where(
                    models.RoomAllocation.section_id == section_id,
                    models.RoomAllocation.room_id == room_id,
                )
            ).scalar_one_or_none()
            if existing is None:
                existing = models.RoomAllocation(
                    section_id=section_id,
                    room_id=room_id,
                    allocated_by_user_id=allocated_by_user_id,
                    notes=payload.notes,
                )
                self.db.add(existing)
            else:
                existing.notes = payload.notes
            rows.append(existing)
        self.db.commit()
        return [self._allocation_read(row) for row in rows]

    def list_allocations(self, section_id: int) -> list[schemas.RoomAllocationRead]:
        self._get_section(section_id)
        allocations = list(
            self.db.execute(
                select(models.RoomAllocation).where(
                    models.RoomAllocation.section_id == section_id
                )
            ).scalars()
        )
        return [self._allocation_read(a) for a in allocations]

    def list_professor_sections(self, user_id: int) -> list[schemas.ProfessorSectionRead]:
        professor = self._get_professor_by_user(user_id)
        stmt = select(models.Section).where(models.Section.professor_id == professor.id)
        sections = list(self.db.execute(stmt).scalars())
        return [self._professor_section_read(section) for section in sections]

    def room_options(self, *, user_id: int, section_id: int) -> schemas.RoomOptionsResponse:
        professor = self._get_professor_by_user(user_id)
        section = self._get_section(section_id)
        if section.professor_id != professor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your section.")
        allocations = list(
            self.db.execute(
                select(models.RoomAllocation).where(models.RoomAllocation.section_id == section_id)
            ).scalars()
        )
        return schemas.RoomOptionsResponse(
            section_id=section.id,
            room_selection_mode=section.room_selection_mode,
            options=[self._allocation_read(allocation) for allocation in allocations],
        )

    def choose_room(
        self,
        *,
        user_id: int,
        section_id: int,
        payload: schemas.RoomPreferenceCreate,
    ) -> schemas.RoomPreferenceRead:
        professor = self._get_professor_by_user(user_id)
        section = self._get_section(section_id)
        if section.professor_id != professor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your section.")
        if section.room_selection_mode == "admin_fixed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This section uses admin_fixed room selection.",
            )
        allocation = self.db.execute(
            select(models.RoomAllocation).where(
                models.RoomAllocation.section_id == section_id,
                models.RoomAllocation.room_id == payload.room_id,
            )
        ).scalar_one_or_none()
        if allocation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room is not allocated to this section.",
            )
        room = self.db.get(models.Room, payload.room_id)
        if room is None or room.capacity < section.capacity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Room cannot fit this section.",
            )
        preference = self.db.execute(
            select(models.ProfessorRoomPreference).where(
                models.ProfessorRoomPreference.section_id == section_id,
                models.ProfessorRoomPreference.professor_id == professor.id,
                models.ProfessorRoomPreference.room_id == payload.room_id,
            )
        ).scalar_one_or_none()
        if preference is None:
            preference = models.ProfessorRoomPreference(
                section_id=section_id,
                professor_id=professor.id,
                room_id=payload.room_id,
                preference_rank=payload.preference_rank,
                status="selected",
            )
            self.db.add(preference)
        else:
            preference.preference_rank = payload.preference_rank
            preference.status = "selected"
        self.db.add(
            models.AuditLog(
                actor_student_id=None,
                event_type="professor_room_selected",
                entity_type="section",
                entity_id=section_id,
                payload={"professor_id": professor.id, "room_id": payload.room_id},
            )
        )
        self.db.commit()
        return schemas.RoomPreferenceRead(
            status="selected",
            message="Room preference saved.",
            section_id=section_id,
            room_id=payload.room_id,
            preference_rank=payload.preference_rank,
        )

    # ── helpers ───────────────────────────────────────────────────────────────

    def _get_section(self, section_id: int) -> models.Section:
        section = self.db.get(models.Section, section_id)
        if section is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found.")
        return section

    def _get_professor_by_user(self, user_id: int) -> models.Professor:
        professor = self.db.execute(
            select(models.Professor).where(models.Professor.user_id == user_id)
        ).scalar_one_or_none()
        if professor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Professor profile not found.",
            )
        return professor

    def _professor_read(
        self, professor: models.Professor, user: models.User | None = None
    ) -> schemas.ProfessorRead:
        user = user or self.db.get(models.User, professor.user_id)
        return schemas.ProfessorRead(
            id=professor.id,
            user_id=professor.user_id,
            email=user.email if user else None,
            full_name=professor.full_name,
            department_name=professor.department_name,
        )

    def _room_read(self, room: models.Room) -> schemas.RoomRead:
        return schemas.RoomRead(
            id=room.id,
            building=room.building,
            room_number=room.room_number,
            capacity=room.capacity,
            room_type=room.room_type,
            is_active=room.is_active,
        )

    def _allocation_read(self, allocation: models.RoomAllocation) -> schemas.RoomAllocationRead:
        room = self.db.get(models.Room, allocation.room_id)
        if room is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found.")
        return schemas.RoomAllocationRead(
            section_id=allocation.section_id,
            room_id=room.id,
            building=room.building,
            room_number=room.room_number,
            capacity=room.capacity,
            room_type=room.room_type,
            available=True,
        )

    def _professor_section_read(self, section: models.Section) -> schemas.ProfessorSectionRead:
        offering = self.db.get(models.CourseOffering, section.course_offering_id)
        course = self.db.get(models.Course, offering.course_id) if offering else None
        return schemas.ProfessorSectionRead(
            section_id=section.id,
            course_code=course.code if course else "UNKNOWN",
            course_title=course.title if course else "Unknown course",
            section_code=section.section_code,
            capacity=section.capacity,
            room_selection_mode=section.room_selection_mode,
            status=section.status,
        )
