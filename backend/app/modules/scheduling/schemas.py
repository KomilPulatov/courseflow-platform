from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.rooms.schemas import RoomRead


class SuggestionRunCreate(BaseModel):
    semester_id: int = Field(gt=0)
    strategy: str = "balanced_heuristic"


class SuggestionItemRead(BaseModel):
    section_id: int
    section_code: str
    course_title: str
    suggested_room: RoomRead | None
    score: float | None
    breakdown: dict | None
    approved: bool

    model_config = {"from_attributes": False}


class SuggestionRunRead(BaseModel):
    run_id: int
    status: str
    semester_id: int
    strategy: str
    created_at: datetime
    completed_at: datetime | None
    items: list[SuggestionItemRead]
