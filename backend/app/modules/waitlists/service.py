from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models
from app.modules.waitlists import schemas


class WaitlistService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_current(self, student_id: int) -> list[schemas.WaitlistItem]:
        entries = list(
            self.db.execute(
                select(models.WaitlistEntry)
                .where(
                    models.WaitlistEntry.student_id == student_id,
                    models.WaitlistEntry.status == "waiting",
                )
                .order_by(models.WaitlistEntry.created_at)
            ).scalars()
        )
        return [self._read(entry) for entry in entries]

    def join(self, student_id: int, payload: schemas.WaitlistCreate) -> schemas.WaitlistItem:
        section = self.db.get(models.Section, payload.section_id)
        if section is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found.")
        existing = self.db.execute(
            select(models.WaitlistEntry).where(
                models.WaitlistEntry.student_id == student_id,
                models.WaitlistEntry.section_id == payload.section_id,
                models.WaitlistEntry.status == "waiting",
            )
        ).scalar_one_or_none()
        if existing is not None:
            return self._read(existing)
        position = (
            int(
                self.db.execute(
                    select(func.count())
                    .select_from(models.WaitlistEntry)
                    .where(
                        models.WaitlistEntry.section_id == payload.section_id,
                        models.WaitlistEntry.status == "waiting",
                    )
                ).scalar_one()
            )
            + 1
        )
        entry = models.WaitlistEntry(
            student_id=student_id,
            section_id=payload.section_id,
            position=position,
            status="waiting",
        )
        self.db.add(entry)
        self.db.commit()
        return self._read(entry)

    def cancel(self, student_id: int, waitlist_entry_id: int) -> schemas.WaitlistDeleteResponse:
        entry = self.db.get(models.WaitlistEntry, waitlist_entry_id)
        if entry is None or entry.student_id != student_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Waitlist entry not found.",
            )
        entry.status = "cancelled"
        self.db.commit()
        return schemas.WaitlistDeleteResponse(status="cancelled", waitlist_entry_id=entry.id)

    def _read(self, entry: models.WaitlistEntry) -> schemas.WaitlistItem:
        return schemas.WaitlistItem(
            waitlist_entry_id=entry.id,
            section_id=entry.section_id,
            position=entry.position,
            status=entry.status,
        )
