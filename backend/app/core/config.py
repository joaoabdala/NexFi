from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "sqlite:///./dev.db"

    SECRET_KEY: str = "insecure-dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ORIGINS: str = "http://localhost:5173"

    APP_TIMEZONE: str = "America/Sao_Paulo"
    DEFAULT_CURRENCY: str = "BRL"
    DEFAULT_LOCALE: str = "pt-BR"
    RECURRENCE_HORIZON_MONTHS: int = 3

    SEED_ADMIN_EMAIL: str = "demo@abdalanexus.com"
    SEED_ADMIN_PASSWORD: str = "demo123"
    SEED_ADMIN_NAME: str = "Usuário Demo"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
