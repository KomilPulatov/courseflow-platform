from typing import Literal

from pydantic import BaseModel, Field


class SuggestionRunCreate(BaseModel):
    semester_id: int = Field(gt=0)
    strategy: str = Field(default="balanced_heuristic", min_length=2, max_length=80)


class SuggestionRunStartResponse(BaseModel):
    run_id: int
    status: Literal["queued", "running", "completed", "approved", "failed"]


class SuggestionItemRead(BaseModel):
    id: int
    section_id: int
    room_id: int | None
    time_slot_id: int | None
    score: int
    reasons: dict | None
    status: str


class SuggestionRunRead(BaseModel):
    id: int
    semester_id: int
    strategy: str
    status: str
    items: list[SuggestionItemRead]


class SuggestionApproveResponse(BaseModel):
    run_id: int
    status: Literal["approved"]
    approved_items: int
