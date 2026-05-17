from pydantic import BaseModel


class PublicAppSettingsRead(BaseModel):
    app_name: str
    version: str
    environment: str
    docs_url: str
    openapi_url: str
    health_url: str
    dependency_health_url: str
    database_backend: str
    observability_enabled: bool
    portal_origin: str
    default_professor_landing: str
    support_email: str
    support_phone: str

