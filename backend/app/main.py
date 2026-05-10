from fastapi import FastAPI

# Import all models so Alembic and SQLAlchemy are aware of them
import app.modules.auth.models  # noqa: F401
import app.modules.courses.models  # noqa: F401
import app.modules.students.models  # noqa: F401
from app.api.v1.router import api_router

app = FastAPI(
    title="CRSP API",
    description="Course Registration and Scheduling Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
