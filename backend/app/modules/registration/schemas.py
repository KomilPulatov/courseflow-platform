from typing import Literal

from pydantic import BaseModel, Field


class RegistrationCreate(BaseModel):
    section_id: int = Field(gt=0)
    idempotency_key: str = Field(min_length=8, max_length=120)


class EligibilityCheck(BaseModel):
    rule: str
    status: Literal["passed", "failed", "skipped"]
    message: str


class EligibilityResponse(BaseModel):
    section_id: int
    eligible: bool
    profile_source: Literal["ins_verified", "manual"]
    gpa_rules_enabled: bool
    checks: list[EligibilityCheck]


class EnrolledResponse(BaseModel):
    status: Literal["enrolled"] = "enrolled"
    enrollment_id: int
    section_id: int
    remaining_seats: int


class WaitlistedResponse(BaseModel):
    status: Literal["waitlisted"] = "waitlisted"
    waitlist_entry_id: int
    position: int


RegistrationDecisionResponse = EnrolledResponse | WaitlistedResponse


class RegistrationListItem(BaseModel):
    enrollment_id: int
    section_id: int
    course_id: int
    course_code: str
    course_title: str
    semester_id: int
    semester_name: str
    status: str


class TimetableItem(BaseModel):
    enrollment_id: int
    section_id: int
    course_code: str
    course_title: str
    day_of_week: str
    start_time: str
    end_time: str


class ErrorResponse(BaseModel):
    error: str
    message: str
