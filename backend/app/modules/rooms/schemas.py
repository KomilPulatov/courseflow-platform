from pydantic import BaseModel, Field


class RoomCreate(BaseModel):
    building: str | None = None
    room_number: str = Field(min_length=1, max_length=40)
    capacity: int = Field(gt=0)
    room_type: str = Field(default="lecture", max_length=40)


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


class RoomAllocationRead(BaseModel):
    id: int
    section_id: int
    room_id: int
    is_preferred: bool
    room: RoomRead

    model_config = {"from_attributes": True}


class RoomOptionRead(BaseModel):
    room_id: int
    building: str | None
    room_number: str
    capacity: int
    room_type: str
    available: bool
