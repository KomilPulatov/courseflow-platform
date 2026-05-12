from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.logging import configure_logging, get_logger
from app.core.telemetry import configure_telemetry, shutdown_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    configure_telemetry(app)
    logger = get_logger("app.startup")
    logger.info("app.started")
    try:
        yield
    finally:
        shutdown_telemetry()
        logger.info("app.stopped")


app = FastAPI(
    title="CRSP API",
    description="Course Registration and Scheduling Platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(api_router, prefix="/api/v1")

demo_dir = Path(__file__).resolve().parents[2] / "frontend"
if demo_dir.exists():
    app.mount("/demo", StaticFiles(directory=demo_dir, html=True), name="demo")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
