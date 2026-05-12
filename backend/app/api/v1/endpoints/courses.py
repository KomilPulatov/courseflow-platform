from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.courses.schemas import CourseDetail, CourseSummary, ErrorResponse, SectionSummary
from app.modules.courses.service import CourseCatalogService

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/",
    response_model=list[CourseSummary],
    responses={400: {"model": ErrorResponse}},
    summary="Browse course catalog",
)
def list_courses(
    db: DbSession,
    semester_id: Annotated[int | None, Query(gt=0)] = None,
    department_id: Annotated[int | None, Query(gt=0)] = None,
    major_id: Annotated[int | None, Query(gt=0)] = None,
    search: str | None = None,
    eligible_only: bool = False,
    x_student_id: Annotated[int | None, Header(alias="X-Student-Id")] = None,
) -> list[CourseSummary]:
    return CourseCatalogService(db).list_public_courses(
        semester_id=semester_id,
        department_id=department_id,
        major_id=major_id,
        search=search,
        eligible_only=eligible_only,
        student_id=x_student_id,
    )


@router.get(
    "/{course_id}",
    response_model=CourseDetail,
    responses={404: {"model": ErrorResponse}},
    summary="Get course detail",
)
def get_course_detail(
    course_id: int,
    db: DbSession,
) -> CourseDetail:
    return CourseCatalogService(db).get_course_detail(course_id)


@router.get(
    "/{course_id}/sections",
    response_model=list[SectionSummary],
    responses={404: {"model": ErrorResponse}},
    summary="List course sections",
)
def list_course_sections(
    course_id: int,
    db: DbSession,
    semester_id: Annotated[int | None, Query(gt=0)] = None,
) -> list[SectionSummary]:
    service = CourseCatalogService(db)
    service.get_course_detail(course_id)
    return service.list_sections(course_id=course_id, semester_id=semester_id)
