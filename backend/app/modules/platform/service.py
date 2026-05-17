from urllib.parse import urlparse

from app.core.config import settings
from app.modules.platform.schemas import PublicAppSettingsRead


class PlatformService:
    def public_app_settings(self) -> PublicAppSettingsRead:
        database_backend = settings.DATABASE_URL.split(":", maxsplit=1)[0]
        portal_origin = self._portal_origin(settings.PORTAL_BASE_URL)
        return PublicAppSettingsRead(
            app_name="Course Registration and Scheduling Platform",
            version=settings.OTEL_SERVICE_VERSION,
            environment=settings.APP_ENV,
            docs_url="/docs",
            openapi_url="/openapi.json",
            health_url="/api/v1/health",
            dependency_health_url="/api/v1/health/dependencies",
            database_backend=database_backend,
            observability_enabled=bool(settings.OTEL_EXPORTER_OTLP_ENDPOINT.strip()),
            portal_origin=portal_origin,
            default_professor_landing="/professor",
            support_email="info@iut.uz",
            support_phone="+998 71 246-05-73",
        )

    @staticmethod
    def _portal_origin(value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return value.rstrip("/")
