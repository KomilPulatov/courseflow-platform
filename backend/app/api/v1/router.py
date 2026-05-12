from fastapi import APIRouter

from app.api.v1.endpoints import admin_catalog, auth, courses, registrations, sections

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(admin_catalog.router, prefix="/admin", tags=["Admin Setup"])
api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
api_router.include_router(registrations.router, prefix="/registrations", tags=["Registrations"])
api_router.include_router(sections.router, prefix="/sections", tags=["Sections"])
