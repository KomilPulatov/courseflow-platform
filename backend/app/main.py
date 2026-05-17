import asyncio
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.endpoints.websocket import router as websocket_router
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.metrics import MetricsMiddleware, metrics_response
from app.core.telemetry import configure_telemetry, shutdown_telemetry
from app.modules.websocket.manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    configure_telemetry(app)
    logger = get_logger("app.startup")
    bridge_stop_event = asyncio.Event()
    bridge_task: asyncio.Task | None = None
    if settings.WEBSOCKET_REDIS_BRIDGE_ENABLED:
        bridge_task = asyncio.create_task(
            manager.listen_for_redis_section_events(bridge_stop_event)
        )
        logger.info("websocket.redis_bridge_started")
    logger.info("app.started")
    try:
        yield
    finally:
        bridge_stop_event.set()
        if bridge_task is not None:
            bridge_task.cancel()
            with suppress(asyncio.CancelledError):
                await bridge_task
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

app.add_middleware(MetricsMiddleware)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(api_router, prefix="/api/v1")
app.include_router(websocket_router)

frontend_dir: Path | None = None
for candidate_dir in (
    Path(__file__).resolve().parents[2] / "frontend" / "dist",
    Path(__file__).resolve().parents[1] / "frontend" / "dist",
    Path(__file__).resolve().parents[2] / "frontend",
    Path(__file__).resolve().parents[1] / "frontend",
):
    if (candidate_dir / "index.html").exists():
        frontend_dir = candidate_dir
        break

if frontend_dir is not None:
    assets_dir = frontend_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/demo", include_in_schema=False)
    @app.get("/demo/{full_path:path}", include_in_schema=False)
    @app.get("/admin", include_in_schema=False)
    @app.get("/admin/{full_path:path}", include_in_schema=False)
    def react_spa(full_path: str = "") -> FileResponse:
        return FileResponse(frontend_dir / "index.html")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


@app.get("/metrics", include_in_schema=False)
def prometheus_metrics():
    return metrics_response()
