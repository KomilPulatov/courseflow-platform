from pydantic import BaseModel


class CompletedCourseOut(BaseModel):
    course_code: str
    course_title: str | None
    grade: str | None
    credits: int | None
    source: str  # ins_verified | manual


class AcademicProfileOut(BaseModel):
    department_name: str | None
    major_name: str | None
    academic_year: int | None
    current_gpa: float | None
    gpa_is_verified: bool
    academic_status: str | None


class StudentProfileResponse(BaseModel):
    student_number: str
    full_name: str
    profile_source: str  # ins_verified | manual
    gpa_rules_enabled: bool  # False for manual students
    academic_profile: AcademicProfileOut | None
    completed_courses: list[CompletedCourseOut]


class ManualProfileUpdateRequest(BaseModel):
    department_name: str
    major_name: str
    academic_year: int
    completed_course_codes: list[str] = []  # e.g. ["MSC1011", "CSE2010"]


class INSSyncRequest(BaseModel):
    password: str
