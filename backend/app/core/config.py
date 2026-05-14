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

    # INS Portal scraper
    PORTAL_BASE_URL: str = "http://ins.inha.uz"
    PORTAL_LOGIN_PATH: str = "/ITIS/Start.aspx"
    PORTAL_GRADES_PATH: str = "/ITIS/STD/SJ/SJ_51001/MarkView_xml.aspx"
    PORTAL_USER_AGENT: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    HTTP_TIMEOUT: float = 30.0
    HTTP_RETRY_TIMES: int = 3

    # Redis keeps short-lived read cache, rate-limit buckets, and WebSocket pub/sub messages.
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False
    REDIS_CACHE_TTL_SECONDS: int = 30
    REDIS_SOCKET_TIMEOUT_SECONDS: float = 0.25

    # RabbitMQ is used through Celery for background registration event handling.
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672//"
    RABBITMQ_ENABLED: bool = False

    WEBSOCKET_REDIS_BRIDGE_ENABLED: bool = False
    REGISTRATION_RATE_LIMIT_ENABLED: bool = False
    REGISTRATION_RATE_LIMIT_PER_MINUTE: int = 60

    # Snapshot storage (raw HTML bytes saved before parsing)
    SNAPSHOT_DIR: str = "./snapshots"

    # Observability
    LOG_LEVEL: str = "INFO"
    METRICS_ENABLED: bool = True
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
