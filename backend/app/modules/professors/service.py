from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import Professor, Section, User
from app.modules.professors.errors import (
    RoomCapacityError,
    RoomConflictError,
    RoomNotInPoolError,
    SectionNotAssignedError,
)
from app.modules.professors.repository import ProfessorRepository
from app.modules.professors.schemas import (
    AssignedSectionRead,
    ProfessorCreate,
    ProfessorRead,
    RoomPreferenceCreate,
    RoomPreferenceRead,
    ScheduleInfo,
)
from app.modules.rooms.repository import RoomRepository
from app.modules.rooms.schemas import RoomRead
from app.modules.rooms.service import RoomService


class ProfessorService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProfessorRepository(db)
        self.room_repo = RoomRepository(db)

    # ── Admin: professor management ──────────────────────────────────────────

    def create_professor(self, data: ProfessorCreate) -> ProfessorRead:
        existing_user = self.db.scalars(
            select(User).where(User.email == data.email)
        ).one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )
        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            role="professor",
            status="active",
        )
        self.db.add(user)
        self.db.flush()

        professor = Professor(
            user_id=user.id,
            full_name=data.full_name,
            department_name=data.department_name,
        )
        self.db.add(professor)
        self.db.flush()
        self.db.commit()
        return ProfessorRead.model_validate(professor)

    def list_professors(self) -> list[ProfessorRead]:
        return [ProfessorRead.model_validate(p) for p in self.repo.list_professors()]

    # ── Professor: own section management ────────────────────────────────────

    def get_professor_or_404(self, user_id: int) -> Professor:
        prof = self.repo.get_professor_by_user_id(user_id)
        if not prof:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Professor profile not found.",
            )
        return prof

    def list_assigned_sections(self, user_id: int) -> list[AssignedSectionRead]:
        prof = self.get_professor_or_404(user_id)
        sections = self.repo.list_sections_by_professor(prof.id)
        return [self._build_section_read(s) for s in sections]

    def get_room_options(self, user_id: int, section_id: int) -> dict:
        prof = self.get_professor_or_404(user_id)
        section = self._get_section_for_professor(section_id, prof.id)
        options = RoomService(self.db).list_section_room_options(section_id)
        return {
            "section_id": section_id,
            "room_selection_mode": section.room_selection_mode,
            "options": [o.model_dump() for o in options],
        }

    def save_room_preference(
        self, user_id: int, section_id: int, data: RoomPreferenceCreate
    ) -> RoomPreferenceRead:
        prof = self.get_professor_or_404(user_id)
        section = self._get_section_for_professor(section_id, prof.id)

        allocation = self.room_repo.get_allocation(section_id, data.room_id)
        if not allocation:
            raise RoomNotInPoolError()

        room = self.room_repo.get_room(data.room_id)
        if room is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found.")
        if room.capacity < section.capacity:
            raise RoomCapacityError()

        section_slots = [
            (s.day_of_week, s.start_time, s.end_time) for s in section.schedules
        ]
        conflicts = self.room_repo.get_sections_using_room_at_slots(room.id, section_slots)
        other_conflicts = [s for s in conflicts if s.id != section_id]
        if other_conflicts:
            raise RoomConflictError()

        pref = self.repo.save_preference(
            section_id=section_id,
            professor_id=prof.id,
            room_id=data.room_id,
            rank=data.preference_rank,
        )
        self.db.commit()
        return RoomPreferenceRead(
            status="selected",
            message="Room preference saved.",
            preference_id=pref.id,
            room=RoomRead.model_validate(room),
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_section_for_professor(self, section_id: int, professor_id: int) -> Section:
        section = self.repo.get_section_for_professor(section_id, professor_id)
        if not section:
            raise SectionNotAssignedError()
        return section

    def _build_section_read(self, section: Section) -> AssignedSectionRead:
        course = section.offering.course
        semester = section.offering.semester
        selected_room = self.room_repo.get_room_for_section(section.id)
        return AssignedSectionRead(
            section_id=section.id,
            section_code=section.section_code,
            course_code=course.code,
            course_title=course.title,
            semester=semester.name,
            capacity=section.capacity,
            room_selection_mode=section.room_selection_mode,
            schedules=[ScheduleInfo.model_validate(s) for s in section.schedules],
            selected_room=RoomRead.model_validate(selected_room) if selected_room else None,
        )
