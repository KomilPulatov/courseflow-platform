from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Room, RoomAllocation, Section, TimetableSuggestionRun
from app.modules.rooms.repository import RoomRepository
from app.modules.scheduling.repository import SchedulingRepository
from app.modules.scheduling.schemas import SuggestionItemRead, SuggestionRunRead
from app.modules.rooms.schemas import RoomRead


class SchedulingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = SchedulingRepository(db)
        self.room_repo = RoomRepository(db)

    def create_suggestion_run(
        self,
        semester_id: int,
        strategy: str,
        admin_user_id: int,
    ) -> SuggestionRunRead:
        semester = self.repo.get_semester(semester_id)
        if not semester:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Semester not found."
            )

        run = self.repo.create_run(
            semester_id=semester_id,
            strategy=strategy,
            created_by_user_id=admin_user_id,
        )

        sections = self.repo.list_open_sections_for_semester(semester_id)
        rooms = list(self.repo.list_active_rooms())

        booked_room_slots: dict[int, list[tuple[str, str, str]]] = {}
        booked_professor_slots: dict[int, list[tuple[str, str, str]]] = {}
        professor_preferences: dict[int, int] = {}

        for sec in sections:
            for pref in sec.room_preferences:
                if pref.status == "selected":
                    professor_preferences[sec.id] = pref.room_id

        items = []
        for section in sections:
            best_room, best_score, best_breakdown = self._pick_best_room(
                section=section,
                rooms=rooms,
                booked_room_slots=booked_room_slots,
                booked_professor_slots=booked_professor_slots,
                professor_preferences=professor_preferences,
            )

            item = self.repo.create_item(
                run_id=run.id,
                section_id=section.id,
                suggested_room_id=best_room.id if best_room else None,
                score=best_score,
                breakdown=best_breakdown,
            )
            items.append((item, section, best_room))

            if best_room and best_score is not None and best_score >= 0:
                for sched in section.schedules:
                    slot = (sched.day_of_week, sched.start_time, sched.end_time)
                    booked_room_slots.setdefault(best_room.id, []).append(slot)
                if section.professor_id:
                    for sched in section.schedules:
                        slot = (sched.day_of_week, sched.start_time, sched.end_time)
                        booked_professor_slots.setdefault(section.professor_id, []).append(slot)

        run.status = "completed"
        run.completed_at = datetime.now(UTC)
        self.db.commit()

        return self._build_run_read(run, items)

    def get_run(self, run_id: int) -> SuggestionRunRead:
        run = self.repo.get_run(run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion run not found."
            )
        items_with_data = [
            (item, item.section, item.suggested_room) for item in run.items
        ]
        return self._build_run_read(run, items_with_data)

    def approve_run(self, run_id: int, admin_user_id: int) -> SuggestionRunRead:
        run = self.repo.get_run(run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion run not found."
            )

        raw_items = self.repo.list_items_for_run(run_id)
        for item in raw_items:
            item.approved = True
            if item.suggested_room_id is not None:
                existing = self.room_repo.get_allocation(item.section_id, item.suggested_room_id)
                if existing:
                    existing.is_preferred = True
                else:
                    self.room_repo.create_allocation(
                        section_id=item.section_id,
                        room_id=item.suggested_room_id,
                        user_id=admin_user_id,
                        is_preferred=True,
                    )

        self.db.commit()

        self.db.refresh(run)
        raw_items_refreshed = self.repo.list_items_for_run(run_id)
        items_with_data = [
            (item, item.section, item.suggested_room) for item in raw_items_refreshed
        ]
        return self._build_run_read(run, items_with_data)

    # ── Scoring algorithm ─────────────────────────────────────────────────────

    def _pick_best_room(
        self,
        section: Section,
        rooms: list[Room],
        booked_room_slots: dict[int, list[tuple[str, str, str]]],
        booked_professor_slots: dict[int, list[tuple[str, str, str]]],
        professor_preferences: dict[int, int],
    ) -> tuple[Room | None, float | None, dict | None]:
        if not section.schedules:
            return None, None, {"reason": "no_schedule"}

        candidate_room_ids: set[int] = set()
        for alloc in section.room_allocations:
            candidate_room_ids.add(alloc.room_id)

        candidates = [r for r in rooms if r.id in candidate_room_ids] if candidate_room_ids else rooms

        best_room: Room | None = None
        best_score = float("-inf")
        best_breakdown: dict | None = None

        for room in candidates:
            score, breakdown = self._score_room_for_section(
                section=section,
                room=room,
                booked_room_slots=booked_room_slots,
                booked_professor_slots=booked_professor_slots,
                professor_preferences=professor_preferences,
            )
            if score > best_score:
                best_score = score
                best_room = room
                best_breakdown = breakdown

        if best_room is None:
            return None, None, {"reason": "no_rooms_available"}
        return best_room, best_score, best_breakdown

    def _score_room_for_section(
        self,
        section: Section,
        room: Room,
        booked_room_slots: dict[int, list[tuple[str, str, str]]],
        booked_professor_slots: dict[int, list[tuple[str, str, str]]],
        professor_preferences: dict[int, int],
    ) -> tuple[float, dict]:
        breakdown: dict[str, float] = {}

        if room.capacity < section.capacity:
            capacity_fit = 0.0
        else:
            capacity_fit = min(section.capacity / room.capacity, 1.0)
        breakdown["capacity_fit"] = capacity_fit

        pref_match = 1.0 if professor_preferences.get(section.id) == room.id else 0.0
        breakdown["professor_preference_match"] = pref_match

        course_type = section.offering.course.course_type or "lecture"
        group_fit = 1.0 if room.room_type == course_type else 0.5
        breakdown["required_course_group_fit"] = group_fit

        room_penalty = 0.0
        for sched in section.schedules:
            slot = (sched.day_of_week, sched.start_time, sched.end_time)
            for booked in booked_room_slots.get(room.id, []):
                if _slots_overlap(slot, booked):
                    room_penalty = 10.0
                    break
        breakdown["room_conflict_penalty"] = room_penalty

        prof_penalty = 0.0
        if section.professor_id:
            for sched in section.schedules:
                slot = (sched.day_of_week, sched.start_time, sched.end_time)
                for booked in booked_professor_slots.get(section.professor_id, []):
                    if _slots_overlap(slot, booked):
                        prof_penalty = 10.0
                        break
        breakdown["professor_conflict_penalty"] = prof_penalty

        total = capacity_fit + pref_match + group_fit - room_penalty - prof_penalty
        return total, breakdown

    # ── Response builder ──────────────────────────────────────────────────────

    def _build_run_read(
        self,
        run: TimetableSuggestionRun,
        items_with_data: list[tuple],
    ) -> SuggestionRunRead:
        item_reads = []
        for item, section, room in items_with_data:
            item_reads.append(
                SuggestionItemRead(
                    section_id=section.id if section else item.section_id,
                    section_code=section.section_code if section else "",
                    course_title=(
                        section.offering.course.title
                        if section and section.offering and section.offering.course
                        else ""
                    ),
                    suggested_room=RoomRead.model_validate(room) if room else None,
                    score=float(item.score) if item.score is not None else None,
                    breakdown=item.breakdown,
                    approved=item.approved,
                )
            )
        return SuggestionRunRead(
            run_id=run.id,
            status=run.status,
            semester_id=run.semester_id,
            strategy=run.strategy,
            created_at=run.created_at,
            completed_at=run.completed_at,
            items=item_reads,
        )


def _slots_overlap(a: tuple[str, str, str], b: tuple[str, str, str]) -> bool:
    day_a, start_a, end_a = a
    day_b, start_b, end_b = b
    if day_a != day_b:
        return False
    return start_a < end_b and start_b < end_a
