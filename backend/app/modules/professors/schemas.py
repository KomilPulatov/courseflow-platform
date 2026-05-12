from pydantic import BaseModel, EmailStr, Field

from app.modules.rooms.schemas import RoomRead


class ProfessorCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=1, max_length=255)
    department_name: str | None = None


class ProfessorRead(BaseModel):
    id: int
    user_id: int
    full_name: str
    department_name: str | None

    model_config = {"from_attributes": True}


class ScheduleInfo(BaseModel):
    day_of_week: str
    start_time: str
    end_time: str

    model_config = {"from_attributes": True}


class AssignedSectionRead(BaseModel):
    section_id: int
    section_code: str
    course_code: str
    course_title: str
    semester: str
    capacity: int
    room_selection_mode: str
    schedules: list[ScheduleInfo]
    selected_room: RoomRead | None


class RoomPreferenceCreate(BaseModel):
    room_id: int = Field(gt=0)
    preference_rank: int = Field(default=1, ge=1)


class RoomPreferenceRead(BaseModel):
    status: str
    message: str
    preference_id: int
    room: RoomRead
