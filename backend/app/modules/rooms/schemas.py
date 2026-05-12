from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ProfessorCreate(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    full_name: str = Field(min_length=2, max_length=255)
    department_name: str | None = Field(default=None, max_length=255)
    password: str = Field(default="prof12345", min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("full_name", "department_name")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class ProfessorRead(BaseModel):
    id: int
    user_id: int
    email: str | None
    full_name: str
    department_name: str | None

    model_config = {"from_attributes": True}


class RoomCreate(BaseModel):
    building: str | None = Field(default=None, max_length=80)
    room_number: str = Field(min_length=1, max_length=40)
    capacity: int = Field(gt=0, le=1000)
    room_type: str = Field(default="lecture", min_length=1, max_length=40)
    is_active: bool = True

    @field_validator("building", "room_number", "room_type")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class RoomRead(BaseModel):
    id: int
    building: str | None
    room_number: str
    capacity: int
    room_type: str
    is_active: bool

    model_config = {"from_attributes": True}


class RoomAllocationCreate(BaseModel):
    room_ids: list[int] = Field(min_length=1)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("room_ids")
    @classmethod
    def dedupe_room_ids(cls, value: list[int]) -> list[int]:
        room_ids = list(dict.fromkeys(value))
        if any(room_id <= 0 for room_id in room_ids):
            raise ValueError("room_ids must be positive integers.")
        return room_ids


class RoomAllocationRead(BaseModel):
    section_id: int
    room_id: int
    building: str | None
    room_number: str
    capacity: int
    room_type: str
    available: bool = True


class ProfessorSectionRead(BaseModel):
    section_id: int
    course_code: str
    course_title: str
    section_code: str
    capacity: int
    room_selection_mode: str
    status: str


class RoomOptionsResponse(BaseModel):
    section_id: int
    room_selection_mode: str
    options: list[RoomAllocationRead]


PreferenceStatus = Literal["selected", "cancelled"]


class RoomPreferenceCreate(BaseModel):
    room_id: int = Field(gt=0)
    preference_rank: int = Field(default=1, gt=0)


class RoomPreferenceRead(BaseModel):
    status: PreferenceStatus
    message: str
    section_id: int
    room_id: int
    preference_rank: int
