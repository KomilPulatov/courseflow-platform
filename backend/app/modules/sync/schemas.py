from datetime import datetime

from pydantic import BaseModel


class SyncRequest(BaseModel):
    username: str
    password: str
    user_id: str


class SyncJobResponse(BaseModel):
    job_id: str
    status: str


class SyncStatusResponse(BaseModel):
    job_id: str
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    failure_code: str | None = None
    safe_message: str | None = None


class TranscriptCourseOut(BaseModel):
    external_id: str
    code: str
    title: str
    credits: int
    grade: str


class TranscriptGpaOut(BaseModel):
    semester: str
    gpa: float
    earned_credits: int


class TranscriptStudentOut(BaseModel):
    student_number: str
    full_name: str
    department_name: str
    major_name: str
    year_standing: str
    cumulative_gpa: float


class TranscriptResponse(BaseModel):
    student: TranscriptStudentOut
    gpa: dict
    courses: list[TranscriptCourseOut]
