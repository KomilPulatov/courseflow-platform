from fastapi import APIRouter

from app.api.v1.endpoints import courses, registrations, sections

api_router = APIRouter()

api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
api_router.include_router(registrations.router, prefix="/registrations", tags=["Registrations"])
api_router.include_router(sections.router, prefix="/sections", tags=["Sections"])
