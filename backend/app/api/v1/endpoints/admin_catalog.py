from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.modules.auth.dependencies import require_admin
from app.modules.courses.schemas import (
    CourseCreate,
    CourseDetail,
    CourseEligibilityRuleCreate,
    CourseEligibilityRuleRead,
    CourseOfferingCreate,
    CourseOfferingRead,
    CoursePrerequisiteRead,
    CourseSummary,
    DepartmentCreate,
    DepartmentRead,
    ErrorResponse,
    MajorCreate,
    MajorRead,
    PrerequisiteReplaceRequest,
    RegistrationPeriodCreate,
    RegistrationPeriodRead,
    SectionCreate,
    SectionSummary,
    SemesterCreate,
    SemesterRead,
)
from app.modules.courses.service import CourseCatalogService
from app.modules.rooms.schemas import (
    ProfessorCreate,
    ProfessorRead,
    RoomAllocationCreate,
    RoomAllocationRead,
    RoomCreate,
    RoomRead,
)
from app.modules.rooms.service import RoomService

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[User, Depends(require_admin)]


@router.get("/departments", response_model=list[DepartmentRead])
def list_departments(_admin: AdminUser, db: DbSession) -> list[DepartmentRead]:
    return CourseCatalogService(db).list_departments()


@router.post(
    "/departments",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
def create_department(
    payload: DepartmentCreate,
    _admin: AdminUser,
    db: DbSession,
) -> DepartmentRead:
    return CourseCatalogService(db).create_department(payload)


@router.get("/majors", response_model=list[MajorRead])
def list_majors(
    _admin: AdminUser,
    db: DbSession,
    department_id: Annotated[int | None, Query(gt=0)] = None,
) -> list[MajorRead]:
    return CourseCatalogService(db).list_majors(department_id=department_id)


@router.post(
    "/majors",
    response_model=MajorRead,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def create_major(payload: MajorCreate, _admin: AdminUser, db: DbSession) -> MajorRead:
    return CourseCatalogService(db).create_major(payload)


@router.get("/semesters", response_model=list[SemesterRead])
def list_semesters(_admin: AdminUser, db: DbSession) -> list[SemesterRead]:
    return CourseCatalogService(db).list_semesters()


@router.post(
    "/semesters",
    response_model=SemesterRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
def create_semester(payload: SemesterCreate, _admin: AdminUser, db: DbSession) -> SemesterRead:
    return CourseCatalogService(db).create_semester(payload)


@router.get("/courses", response_model=list[CourseSummary])
def list_admin_courses(_admin: AdminUser, db: DbSession) -> list[CourseSummary]:
    return CourseCatalogService(db).list_admin_courses()


@router.post(
    "/courses",
    response_model=CourseDetail,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def create_course(payload: CourseCreate, _admin: AdminUser, db: DbSession) -> CourseDetail:
    return CourseCatalogService(db).create_course(payload)


@router.put(
    "/courses/{course_id}/prerequisites",
    response_model=list[CoursePrerequisiteRead],
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def replace_course_prerequisites(
    course_id: int,
    payload: PrerequisiteReplaceRequest,
    _admin: AdminUser,
    db: DbSession,
) -> list[CoursePrerequisiteRead]:
    return CourseCatalogService(db).replace_prerequisites(course_id, payload)


@router.post(
    "/courses/{course_id}/eligibility-rules",
    response_model=CourseEligibilityRuleRead,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}},
)
def create_course_eligibility_rule(
    course_id: int,
    payload: CourseEligibilityRuleCreate,
    _admin: AdminUser,
    db: DbSession,
) -> CourseEligibilityRuleRead:
    return CourseCatalogService(db).create_eligibility_rule(course_id, payload)


@router.get("/course-offerings", response_model=list[CourseOfferingRead])
def list_course_offerings(
    _admin: AdminUser,
    db: DbSession,
    semester_id: Annotated[int | None, Query(gt=0)] = None,
) -> list[CourseOfferingRead]:
    return CourseCatalogService(db).list_course_offerings(semester_id=semester_id)


@router.post(
    "/course-offerings",
    response_model=CourseOfferingRead,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def create_course_offering(
    payload: CourseOfferingCreate,
    _admin: AdminUser,
    db: DbSession,
) -> CourseOfferingRead:
    return CourseCatalogService(db).create_course_offering(payload)


@router.get("/sections", response_model=list[SectionSummary])
def list_sections(
    _admin: AdminUser,
    db: DbSession,
    course_id: Annotated[int | None, Query(gt=0)] = None,
    semester_id: Annotated[int | None, Query(gt=0)] = None,
) -> list[SectionSummary]:
    return CourseCatalogService(db).list_sections(course_id=course_id, semester_id=semester_id)


@router.post(
    "/sections",
    response_model=SectionSummary,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def create_section(payload: SectionCreate, _admin: AdminUser, db: DbSession) -> SectionSummary:
    return CourseCatalogService(db).create_section(payload)


@router.post(
    "/professors",
    response_model=ProfessorRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
def create_professor(
    payload: ProfessorCreate,
    _admin: AdminUser,
    db: DbSession,
) -> ProfessorRead:
    return RoomService(db).create_professor(payload)


@router.post(
    "/rooms",
    response_model=RoomRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
def create_room(payload: RoomCreate, _admin: AdminUser, db: DbSession) -> RoomRead:
    return RoomService(db).create_room(payload)


@router.post(
    "/sections/{section_id}/room-allocations",
    response_model=list[RoomAllocationRead],
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def allocate_rooms(
    section_id: int,
    payload: RoomAllocationCreate,
    current_user: AdminUser,
    db: DbSession,
) -> list[RoomAllocationRead]:
    return RoomService(db).allocate_rooms(
        section_id=section_id,
        payload=payload,
        allocated_by_user_id=current_user.id,
    )


@router.get("/registration-periods", response_model=list[RegistrationPeriodRead])
def list_registration_periods(
    _admin: AdminUser,
    db: DbSession,
    semester_id: Annotated[int | None, Query(gt=0)] = None,
) -> list[RegistrationPeriodRead]:
    return CourseCatalogService(db).list_registration_periods(semester_id=semester_id)


@router.post(
    "/registration-periods",
    response_model=RegistrationPeriodRead,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def create_registration_period(
    payload: RegistrationPeriodCreate,
    _admin: AdminUser,
    db: DbSession,
) -> RegistrationPeriodRead:
    return CourseCatalogService(db).create_registration_period(payload)
