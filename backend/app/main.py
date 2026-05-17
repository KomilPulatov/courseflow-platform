from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.endpoints.websocket import router as websocket_router
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
app.include_router(websocket_router)

demo_dir = Path(__file__).resolve().parents[2] / "frontend"
if demo_dir.exists():
    app.mount("/demo", StaticFiles(directory=demo_dir, html=True), name="demo")

professor_dir = demo_dir / "professor"
professor_assets_dir = professor_dir / "assets"
if professor_assets_dir.exists():
    app.mount("/portal-assets", StaticFiles(directory=professor_assets_dir), name="portal-assets")

professor_dist_dir = professor_dir / "dist"
if professor_dist_dir.exists():
    app.mount("/professor-static", StaticFiles(directory=professor_dist_dir), name="professor-static")

app_shell_dir = demo_dir / "app-shell"
app_shell_dist_dir = app_shell_dir / "dist"
if app_shell_dist_dir.exists():
    app.mount("/app-static", StaticFiles(directory=app_shell_dist_dir), name="app-static")


def professor_page_response() -> FileResponse:
    return FileResponse(professor_dist_dir / "index.html")


def app_shell_page_response() -> FileResponse:
    return FileResponse(app_shell_dist_dir / "index.html")


@app.get("/professor", include_in_schema=False)
def professor_dashboard_page() -> FileResponse:
    return professor_page_response()


@app.get("/professor/{full_path:path}", include_in_schema=False)
def professor_app_routes(full_path: str) -> FileResponse:
    return professor_page_response()


@app.get("/app", include_in_schema=False)
def app_shell_root() -> FileResponse:
    return app_shell_page_response()


@app.get("/app/{full_path:path}", include_in_schema=False)
def app_shell_routes(full_path: str) -> FileResponse:
    return app_shell_page_response()


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
