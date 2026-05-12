from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db import models
from app.modules.scheduling import schemas


class SchedulingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_run(
        self, payload: schemas.SuggestionRunCreate, requested_by_user_id: int
    ) -> schemas.SuggestionRunStartResponse:
        if self.db.get(models.Semester, payload.semester_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semester not found.")
        run = models.TimetableSuggestionRun(
            semester_id=payload.semester_id,
            strategy=payload.strategy,
            status="running",
            requested_by_user_id=requested_by_user_id,
        )
        self.db.add(run)
        self.db.flush()

        self._generate_items_heuristic(run)

        run.status = "completed"
        run.completed_at = datetime.now(UTC)
        self.db.commit()
        return schemas.SuggestionRunStartResponse(run_id=run.id, status=run.status)

    def get_run(self, run_id: int) -> schemas.SuggestionRunRead:
        run = self._get_run(run_id)
        items = list(
            self.db.execute(
                select(models.TimetableSuggestionItem).where(
                    models.TimetableSuggestionItem.run_id == run_id
                )
            ).scalars()
        )
        return schemas.SuggestionRunRead(
            id=run.id,
            semester_id=run.semester_id,
            strategy=run.strategy,
            status=run.status,
            items=[
                schemas.SuggestionItemRead(
                    id=item.id,
                    section_id=item.section_id,
                    room_id=item.room_id,
                    time_slot_id=item.time_slot_id,
                    score=item.score,
                    reasons=item.reasons,
                    status=item.status,
                )
                for item in items
            ],
        )

    def approve_run(self, run_id: int) -> schemas.SuggestionApproveResponse:
        run = self._get_run(run_id)
        items = list(
            self.db.execute(
                select(models.TimetableSuggestionItem).where(
                    models.TimetableSuggestionItem.run_id == run_id
                )
            ).scalars()
        )
        approved = 0
        for item in items:
            if item.room_id is None:
                continue
            existing_alloc = self.db.execute(
                select(models.RoomAllocation).where(
                    models.RoomAllocation.section_id == item.section_id,
                    models.RoomAllocation.room_id == item.room_id,
                )
            ).scalar_one_or_none()
            if existing_alloc:
                existing_alloc.is_preferred = True
            else:
                self.db.add(
                    models.RoomAllocation(
                        section_id=item.section_id,
                        room_id=item.room_id,
                        is_preferred=True,
                    )
                )
            item.status = "approved"
            approved += 1
        run.status = "approved"
        run.approved_at = datetime.now(UTC)
        self.db.commit()
        return schemas.SuggestionApproveResponse(
            run_id=run.id, status="approved", approved_items=approved
        )

    # ── Heuristic algorithm ───────────────────────────────────────────────────

    def _generate_items_heuristic(self, run: models.TimetableSuggestionRun) -> None:
        sections = list(
            self.db.execute(
                select(models.Section)
                .join(
                    models.CourseOffering,
                    models.CourseOffering.id == models.Section.course_offering_id,
                )
                .options(
                    joinedload(models.Section.schedules),
                    joinedload(models.Section.offering).joinedload(models.CourseOffering.course),
                    joinedload(models.Section.room_allocations),
                    joinedload(models.Section.room_preferences),
                )
                .where(
                    models.CourseOffering.semester_id == run.semester_id,
                    models.Section.status.in_(["open", "draft"]),
                )
            )
            .unique()
            .scalars()
        )
        rooms = list(
            self.db.execute(select(models.Room).where(models.Room.is_active.is_(True))).scalars()
        )

        booked_room_slots: dict[int, list[tuple[str, str, str]]] = {}
        booked_professor_slots: dict[int, list[tuple[str, str, str]]] = {}
        professor_preferences: dict[int, int] = {}

        for sec in sections:
            for pref in sec.room_preferences:
                if pref.status == "selected":
                    professor_preferences[sec.id] = pref.room_id

        for section in sections:
            best_room, best_score, breakdown = self._pick_best_room(
                section=section,
                rooms=rooms,
                booked_room_slots=booked_room_slots,
                booked_professor_slots=booked_professor_slots,
                professor_preferences=professor_preferences,
            )

            self.db.add(
                models.TimetableSuggestionItem(
                    run_id=run.id,
                    section_id=section.id,
                    room_id=best_room.id if best_room else None,
                    time_slot_id=None,
                    score=max(0, round(best_score * 100)) if best_score is not None else 0,
                    reasons=breakdown,
                    status="suggested",
                )
            )

            if best_room and best_score is not None and best_score >= 0:
                for sched in section.schedules:
                    slot = (sched.day_of_week, sched.start_time, sched.end_time)
                    booked_room_slots.setdefault(best_room.id, []).append(slot)
                if section.professor_id:
                    for sched in section.schedules:
                        slot = (sched.day_of_week, sched.start_time, sched.end_time)
                        booked_professor_slots.setdefault(section.professor_id, []).append(slot)

        self.db.flush()

    def _pick_best_room(
        self,
        section: models.Section,
        rooms: list[models.Room],
        booked_room_slots: dict[int, list[tuple[str, str, str]]],
        booked_professor_slots: dict[int, list[tuple[str, str, str]]],
        professor_preferences: dict[int, int],
    ) -> tuple[models.Room | None, float | None, dict | None]:
        if not section.schedules:
            return None, None, {"reason": "no_schedule"}

        candidate_ids = {alloc.room_id for alloc in section.room_allocations}
        candidates = [r for r in rooms if r.id in candidate_ids] if candidate_ids else rooms

        best_room: models.Room | None = None
        best_score = float("-inf")
        best_breakdown: dict | None = None

        for room in candidates:
            score, breakdown = self._score_room(
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

    def _score_room(
        self,
        section: models.Section,
        room: models.Room,
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

        course_type = (
            section.offering.course.course_type
            if section.offering and section.offering.course
            else None
        ) or "lecture"
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

    def _get_run(self, run_id: int) -> models.TimetableSuggestionRun:
        run = self.db.get(models.TimetableSuggestionRun, run_id)
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Suggestion run not found.",
            )
        return run


def _slots_overlap(a: tuple[str, str, str], b: tuple[str, str, str]) -> bool:
    day_a, start_a, end_a = a
    day_b, start_b, end_b = b
    if day_a != day_b:
        return False
    return start_a < end_b and start_b < end_a
