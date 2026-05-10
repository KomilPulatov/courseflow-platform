from fastapi import APIRouter

from app.api.v1.endpoints import auth, courses, registration, student_profiles, sync

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(
    student_profiles.router, prefix="/student-profiles", tags=["Student Profiles"]
)
api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
api_router.include_router(registration.router, prefix="/registration", tags=["Registration"])
api_router.include_router(sync.router, prefix="/sync", tags=["Sync"])
