from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.pagination import Page
from app.db.models import User
from app.db.session import get_db
from app.modules.auth.dependencies import require_admin
from app.modules.courses.schemas import (
    CourseCreate,
    CourseDetail,
    CourseEligibilityRuleCreate,
    CourseEligibilityRuleRead,
    CourseEligibilityRuleUpdate,
    CourseOfferingCreate,
    CourseOfferingRead,
    CourseOfferingUpdate,
    CoursePrerequisiteRead,
    CourseSummary,
    CourseUpdate,
    DepartmentCreate,
    DepartmentRead,
    DepartmentUpdate,
    ErrorResponse,
    MajorCreate,
    MajorRead,
    MajorUpdate,
    PrerequisiteReplaceRequest,
    RegistrationPeriodCreate,
    RegistrationPeriodRead,
    RegistrationPeriodUpdate,
    SectionCreate,
    SectionSummary,
    SectionUpdate,
    SemesterCreate,
    SemesterRead,
    SemesterUpdate,
)
from app.modules.courses.service import CourseCatalogService

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


@router.patch(
    "/departments/{department_id}",
    response_model=DepartmentRead,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def update_department(
    department_id: int,
    payload: DepartmentUpdate,
    _admin: AdminUser,
    db: DbSession,
) -> DepartmentRead:
    return CourseCatalogService(db).update_department(department_id, payload)


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


@router.patch(
    "/majors/{major_id}",
    response_model=MajorRead,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def update_major(
    major_id: int,
    payload: MajorUpdate,
    _admin: AdminUser,
    db: DbSession,
) -> MajorRead:
    return CourseCatalogService(db).update_major(major_id, payload)


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


@router.patch(
    "/semesters/{semester_id}",
    response_model=SemesterRead,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def update_semester(
    semester_id: int,
    payload: SemesterUpdate,
    _admin: AdminUser,
    db: DbSession,
) -> SemesterRead:
    return CourseCatalogService(db).update_semester(semester_id, payload)


@router.get("/courses", response_model=Page[CourseSummary])
def list_admin_courses(
    _admin: AdminUser,
    db: DbSession,
    search: str | None = None,
    department_id: Annotated[int | None, Query(gt=0)] = None,
    is_active: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[CourseSummary]:
    return CourseCatalogService(db).list_admin_courses(
        search=search,
        department_id=department_id,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/courses",
    response_model=CourseDetail,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def create_course(payload: CourseCreate, _admin: AdminUser, db: DbSession) -> CourseDetail:
    return CourseCatalogService(db).create_course(payload)


@router.get(
    "/courses/{course_id}",
    response_model=CourseDetail,
    responses={404: {"model": ErrorResponse}},
)
def get_admin_course_detail(
    course_id: int,
    _admin: AdminUser,
    db: DbSession,
) -> CourseDetail:
    return CourseCatalogService(db).get_course_detail(course_id, include_inactive=True)


@router.patch(
    "/courses/{course_id}",
    response_model=CourseDetail,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def update_course(
    course_id: int,
    payload: CourseUpdate,
    _admin: AdminUser,
    db: DbSession,
) -> CourseDetail:
    return CourseCatalogService(db).update_course(course_id, payload)


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


@router.put(
    "/courses/{course_id}/equivalencies",
    response_model=list[CourseEquivalentRead],
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
def replace_course_equivalencies(
    course_id: int,
    payload: CourseEquivalencyReplaceRequest,
    _admin: AdminUser,
    db: DbSession,
) -> list[CourseEquivalentRead]:
    return CourseCatalogService(db).replace_equivalencies(course_id, payload)


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


@router.get(
    "/courses/{course_id}/eligibility-rules",
    response_model=list[CourseEligibilityRuleRead],
    responses={404: {"model": ErrorResponse}},
)
def list_course_eligibility_rules(
    course_id: int,
    _admin: AdminUser,
    db: DbSession,
) -> list[CourseEligibilityRuleRead]:
    return CourseCatalogService(db).list_eligibility_rules(course_id)


@router.patch(
    "/courses/{course_id}/eligibility-rules/{rule_id}",
    response_model=CourseEligibilityRuleRead,
    responses={404: {"model": ErrorResponse}},
)
def update_course_eligibility_rule(
    course_id: int,
    rule_id: int,
    payload: CourseEligibilityRuleUpdate,
    _admin: AdminUser,
    db: DbSession,
) -> CourseEligibilityRuleRead:
    return CourseCatalogService(db).update_eligibility_rule(course_id, rule_id, payload)


@router.delete(
    "/courses/{course_id}/eligibility-rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
def delete_course_eligibility_rule(
    course_id: int,
    rule_id: int,
    _admin: AdminUser,
    db: DbSession,
) -> None:
    CourseCatalogService(db).delete_eligibility_rule(course_id, rule_id)


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


@router.patch(
    "/course-offerings/{offering_id}",
    response_model=CourseOfferingRead,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def update_course_offering(
    offering_id: int,
    payload: CourseOfferingUpdate,
    _admin: AdminUser,
    db: DbSession,
) -> CourseOfferingRead:
    return CourseCatalogService(db).update_course_offering(offering_id, payload)


@router.get("/sections", response_model=Page[SectionSummary])
def list_sections(
    _admin: AdminUser,
    db: DbSession,
    course_id: Annotated[int | None, Query(gt=0)] = None,
    semester_id: Annotated[int | None, Query(gt=0)] = None,
    status_value: Annotated[str | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[SectionSummary]:
    return CourseCatalogService(db).list_sections_page(
        course_id=course_id,
        semester_id=semester_id,
        status_value=status_value,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/sections",
    response_model=SectionSummary,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def create_section(payload: SectionCreate, _admin: AdminUser, db: DbSession) -> SectionSummary:
    return CourseCatalogService(db).create_section(payload)


@router.patch(
    "/sections/{section_id}",
    response_model=SectionSummary,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def update_section(
    section_id: int,
    payload: SectionUpdate,
    _admin: AdminUser,
    db: DbSession,
) -> SectionSummary:
    return CourseCatalogService(db).update_section(section_id, payload)


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


@router.patch(
    "/registration-periods/{period_id}",
    response_model=RegistrationPeriodRead,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def update_registration_period(
    period_id: int,
    payload: RegistrationPeriodUpdate,
    _admin: AdminUser,
    db: DbSession,
) -> RegistrationPeriodRead:
    return CourseCatalogService(db).update_registration_period(period_id, payload)
