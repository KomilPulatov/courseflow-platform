from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router

app = FastAPI(
    title="CRSP API",
    description="Course Registration and Scheduling Platform",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api/v1")

demo_dir = Path(__file__).resolve().parents[2] / "frontend"
if demo_dir.exists():
    app.mount("/demo", StaticFiles(directory=demo_dir, html=True), name="demo")


@app.get("/health")
def health_check():
    return {"status": "ok"}
