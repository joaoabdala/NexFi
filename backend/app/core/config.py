from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_SECRET_KEYS = {"insecure-dev-secret-change-me", "change-this-to-a-random-secret-in-production"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "sqlite:///./dev.db"

    SECRET_KEY: str = "insecure-dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ORIGINS: str = "http://localhost:5173"
    # Regex opcional para origens dinâmicas, ex.: preview deployments da Vercel
    # (https://nexfi-[a-z0-9-]+\.vercel\.app). Vazio = desabilitado.
    CORS_ORIGIN_REGEX: str = ""

    APP_TIMEZONE: str = "America/Sao_Paulo"
    DEFAULT_CURRENCY: str = "BRL"
    DEFAULT_LOCALE: str = "pt-BR"
    RECURRENCE_HORIZON_MONTHS: int = 3

    SEED_ADMIN_EMAIL: str = "demo@abdalanexus.com"
    SEED_ADMIN_PASSWORD: str = "demo123"
    SEED_ADMIN_NAME: str = "Usuário Demo"

    @field_validator("DATABASE_URL")
    @classmethod
    def _use_psycopg3_driver(cls, value: str) -> str:
        # Neon/Vercel entregam "postgresql://" (ou "postgres://"), que o SQLAlchemy mapeia para
        # psycopg2 — não instalado. Força o driver psycopg (v3), que é o do requirements.txt.
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix):]
        return value

    @model_validator(mode="after")
    def _require_real_secret_in_production(self) -> "Settings":
        if self.ENVIRONMENT == "production" and self.SECRET_KEY in _INSECURE_SECRET_KEYS:
            raise ValueError("SECRET_KEY precisa ser definida com um valor aleatório em produção.")
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
