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
    INS_MOCK_ENABLED: bool = True  # Use mock data; set False for real scraper

    @property
    def POSTGRES_DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = {"env_file": "../.env", "extra": "ignore"}


settings = Settings()
