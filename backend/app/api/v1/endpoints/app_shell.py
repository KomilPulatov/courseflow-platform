from fastapi import APIRouter

from app.modules.platform.schemas import PublicAppSettingsRead
from app.modules.platform.service import PlatformService

router = APIRouter()


@router.get("/settings", response_model=PublicAppSettingsRead)
def public_app_settings() -> PublicAppSettingsRead:
    return PlatformService().public_app_settings()
