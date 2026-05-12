from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_catalog,
    auth,
    courses,
    health,
    professor,
    registrations,
    rooms,
    scheduling,
    sections,
    student_profiles,
    sync,
    waitlists,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(admin_catalog.router, prefix="/admin", tags=["Admin Setup"])
api_router.include_router(rooms.router, prefix="/admin", tags=["Rooms"])
api_router.include_router(scheduling.router, prefix="/admin/scheduling", tags=["Scheduling"])
api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
api_router.include_router(professor.router, prefix="/professor", tags=["Professor"])
api_router.include_router(registrations.router, prefix="/registrations", tags=["Registrations"])
api_router.include_router(waitlists.router, prefix="/waitlists", tags=["Waitlists"])
api_router.include_router(sections.router, prefix="/sections", tags=["Sections"])
api_router.include_router(
    student_profiles.router, prefix="/student-profiles", tags=["Student Profiles"]
)
api_router.include_router(sync.router, prefix="/sync", tags=["Sync"])
