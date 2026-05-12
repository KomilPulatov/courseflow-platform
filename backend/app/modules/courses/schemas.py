from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class DepartmentCreate(BaseModel):
    code: str = Field(min_length=2, max_length=20)
    name: str = Field(min_length=2, max_length=255)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()


class DepartmentRead(BaseModel):
    id: int
    code: str
    name: str


class MajorCreate(BaseModel):
    department_id: int = Field(gt=0)
    code: str = Field(min_length=2, max_length=20)
    name: str = Field(min_length=2, max_length=255)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()


class MajorRead(BaseModel):
    id: int
    department_id: int
    code: str
    name: str


SemesterStatus = Literal["draft", "active", "archived"]


class SemesterCreate(BaseModel):
    name: str = Field(min_length=4, max_length=120)
    status: SemesterStatus = "active"

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()


class SemesterRead(BaseModel):
    id: int
    name: str
    status: SemesterStatus


class CourseCreate(BaseModel):
    department_id: int | None = Field(default=None, gt=0)
    code: str = Field(min_length=4, max_length=40)
    title: str = Field(min_length=2, max_length=255)
    credits: int = Field(gt=0, le=12)
    description: str | None = Field(default=None, max_length=5000)
    course_type: str | None = Field(default=None, max_length=40)
    is_repeatable: bool = False

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("title", "description", "course_type")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class CourseReference(BaseModel):
    id: int
    code: str
    title: str


class CourseSummary(BaseModel):
    id: int
    department_id: int | None
    department_code: str | None
    department_name: str | None
    code: str
    title: str
    credits: int
    course_type: str | None
    active_offering_count: int
    active_section_count: int


class CourseDetail(BaseModel):
    id: int
    department_id: int | None
    department_code: str | None
    department_name: str | None
    code: str
    title: str
    credits: int
    description: str | None
    course_type: str | None
    is_repeatable: bool
    prerequisites: list[CourseReference]


class PrerequisiteReplaceRequest(BaseModel):
    prerequisite_course_ids: list[int] = Field(default_factory=list)
    rule_group: Literal["all"] = "all"

    @field_validator("prerequisite_course_ids")
    @classmethod
    def deduplicate_ids(cls, value: list[int]) -> list[int]:
        unique_ids = list(dict.fromkeys(value))
        if any(item <= 0 for item in unique_ids):
            raise ValueError("Prerequisite course ids must be positive integers.")
        return unique_ids


class CoursePrerequisiteRead(BaseModel):
    prerequisite_course_id: int
    prerequisite_code: str
    prerequisite_title: str
    rule_group: str


class CourseEligibilityRuleCreate(BaseModel):
    min_academic_year: int | None = Field(default=None, ge=1, le=6)
    min_gpa: float | None = Field(default=None, ge=0, le=5)
    allowed_department_ids: list[int] | None = None
    allowed_major_ids: list[int] | None = None
    rule_metadata: dict | None = None


class CourseEligibilityRuleRead(BaseModel):
    id: int
    course_id: int
    min_academic_year: int | None
    min_gpa: float | None
    allowed_department_ids: list[int] | None
    allowed_major_ids: list[int] | None
    rule_metadata: dict | None


CourseOfferingStatus = Literal["draft", "active", "cancelled", "archived"]


class CourseOfferingCreate(BaseModel):
    course_id: int = Field(gt=0)
    semester_id: int = Field(gt=0)
    status: CourseOfferingStatus = "active"


class CourseOfferingRead(BaseModel):
    id: int
    course_id: int
    course_code: str
    course_title: str
    semester_id: int
    semester_name: str
    status: CourseOfferingStatus
    section_count: int


SectionStatus = Literal["draft", "open", "closed", "cancelled"]
RoomSelectionMode = Literal["admin_fixed", "professor_choice", "system_recommended"]


class SectionCreate(BaseModel):
    course_offering_id: int = Field(gt=0)
    professor_id: int | None = Field(default=None, gt=0)
    section_code: str = Field(min_length=1, max_length=40)
    capacity: int = Field(gt=0, le=500)
    room_selection_mode: RoomSelectionMode = "admin_fixed"
    status: SectionStatus = "open"

    @field_validator("section_code")
    @classmethod
    def normalize_section_code(cls, value: str) -> str:
        return value.strip().upper()


class SectionSummary(BaseModel):
    id: int
    course_offering_id: int
    course_id: int
    course_code: str
    course_title: str
    semester_id: int
    semester_name: str
    professor_id: int | None
    section_code: str
    capacity: int
    enrolled_count: int
    remaining_seats: int
    waitlist_count: int
    room_selection_mode: RoomSelectionMode
    status: SectionStatus


class SectionAvailability(BaseModel):
    section_id: int
    capacity: int
    enrolled_count: int
    remaining_seats: int
    waitlist_count: int
    status: SectionStatus


RegistrationPeriodStatus = Literal["open", "closed"]


class RegistrationPeriodCreate(BaseModel):
    semester_id: int = Field(gt=0)
    opens_at: datetime
    closes_at: datetime
    status: RegistrationPeriodStatus = "open"

    @model_validator(mode="after")
    def validate_window(self) -> "RegistrationPeriodCreate":
        if self.closes_at <= self.opens_at:
            raise ValueError("closes_at must be later than opens_at.")
        return self


class RegistrationPeriodRead(BaseModel):
    id: int
    semester_id: int
    semester_name: str
    opens_at: datetime
    closes_at: datetime
    status: RegistrationPeriodStatus


class ErrorResponse(BaseModel):
    detail: str
