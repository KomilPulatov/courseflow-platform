from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

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
        self._generate_items(run)
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
            if item.room_id is None or item.time_slot_id is None:
                continue
            time_slot = self.db.get(models.TimeSlot, item.time_slot_id)
            if time_slot is None:
                continue
            schedule = self.db.execute(
                select(models.SectionSchedule).where(
                    models.SectionSchedule.section_id == item.section_id
                )
            ).scalar_one_or_none()
            if schedule is None:
                schedule = models.SectionSchedule(
                    section_id=item.section_id,
                    room_id=item.room_id,
                    time_slot_id=item.time_slot_id,
                    day_of_week=time_slot.day_of_week,
                    start_time=time_slot.start_time,
                    end_time=time_slot.end_time,
                )
                self.db.add(schedule)
            else:
                schedule.room_id = item.room_id
                schedule.time_slot_id = item.time_slot_id
                schedule.day_of_week = time_slot.day_of_week
                schedule.start_time = time_slot.start_time
                schedule.end_time = time_slot.end_time
            item.status = "approved"
            approved += 1
        run.status = "approved"
        run.approved_at = datetime.now(UTC)
        self.db.commit()
        return schemas.SuggestionApproveResponse(
            run_id=run.id, status="approved", approved_items=approved
        )

    def _generate_items(self, run: models.TimetableSuggestionRun) -> None:
        self._ensure_default_time_slots()
        sections = list(
            self.db.execute(
                select(models.Section)
                .join(
                    models.CourseOffering,
                    models.CourseOffering.id == models.Section.course_offering_id,
                )
                .where(models.CourseOffering.semester_id == run.semester_id)
            ).scalars()
        )
        time_slots = list(self.db.execute(select(models.TimeSlot)).scalars())
        for index, section in enumerate(sections):
            room_id = self._preferred_room_id(section.id) or self._first_allocated_room_id(
                section.id
            )
            time_slot = time_slots[index % len(time_slots)] if time_slots else None
            score = 100 if room_id and time_slot else 25
            self.db.add(
                models.TimetableSuggestionItem(
                    run_id=run.id,
                    section_id=section.id,
                    room_id=room_id,
                    time_slot_id=time_slot.id if time_slot else None,
                    score=score,
                    reasons={
                        "room": "professor_preference_or_first_allocation"
                        if room_id
                        else "missing_room",
                        "time": "round_robin_default_slots" if time_slot else "missing_time_slot",
                    },
                )
            )

    def _ensure_default_time_slots(self) -> None:
        if self.db.execute(select(models.TimeSlot.id)).first() is not None:
            return
        for day, start, end in [
            ("monday", "09:00", "10:20"),
            ("monday", "10:30", "11:50"),
            ("wednesday", "09:00", "10:20"),
            ("wednesday", "10:30", "11:50"),
            ("friday", "09:00", "10:20"),
        ]:
            self.db.add(models.TimeSlot(day_of_week=day, start_time=start, end_time=end))
        self.db.flush()

    def _preferred_room_id(self, section_id: int) -> int | None:
        preference = self.db.execute(
            select(models.ProfessorRoomPreference)
            .where(
                models.ProfessorRoomPreference.section_id == section_id,
                models.ProfessorRoomPreference.status == "selected",
            )
            .order_by(models.ProfessorRoomPreference.preference_rank)
        ).scalar_one_or_none()
        return preference.room_id if preference else None

    def _first_allocated_room_id(self, section_id: int) -> int | None:
        allocation = self.db.execute(
            select(models.RoomAllocation)
            .where(models.RoomAllocation.section_id == section_id)
            .order_by(models.RoomAllocation.id)
        ).scalar_one_or_none()
        return allocation.room_id if allocation else None

    def _get_run(self, run_id: int) -> models.TimetableSuggestionRun:
        run = self.db.get(models.TimetableSuggestionRun, run_id)
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Suggestion run not found.",
            )
        return run
