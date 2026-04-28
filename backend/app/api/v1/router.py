from fastapi import APIRouter

from app.api.v1.endpoints import courses, registration

api_router = APIRouter()

api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
api_router.include_router(registration.router, prefix="/registration", tags=["Registration"])
