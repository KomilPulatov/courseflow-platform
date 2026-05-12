from contextlib import asynccontextmanager

from fastapi import FastAPI

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
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}
