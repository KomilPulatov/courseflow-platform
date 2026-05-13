from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "local"
    SECRET_KEY: str = "change-me-to-a-long-random-string"
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = "sqlite:///./crsp.db"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "crsp"
    POSTGRES_USER: str = "crsp"
    POSTGRES_PASSWORD: str = "crsp"

    # INS Integration
    INS_MOCK_ENABLED: bool = True

    # INS Portal scraper
    PORTAL_BASE_URL: str = "https://ins.inha.uz"
    PORTAL_LOGIN_PATH: str = "/Account/Login"
    PORTAL_GRADES_PATH: str = "/StuAca/ViewGradeStandings"
    PORTAL_USER_AGENT: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    HTTP_TIMEOUT: float = 30.0
    HTTP_RETRY_TIMES: int = 3

    # Redis (ARQ worker queue + per-user sync lock)
    REDIS_URL: str = "redis://localhost:6379/0"
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672//"

    # Snapshot storage (raw HTML bytes saved before parsing)
    SNAPSHOT_DIR: str = "./snapshots"

    # Observability
    LOG_LEVEL: str = "INFO"
    OTEL_SERVICE_NAME: str = "crsp-backend"
    OTEL_SERVICE_VERSION: str = "0.1.0"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""  # empty disables OTel export
    OTEL_EXPORTER_OTLP_INSECURE: bool = True

    @property
    def POSTGRES_DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = {"env_file": "../.env", "extra": "ignore"}


settings = Settings()
