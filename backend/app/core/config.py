import os
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

    @property
    def is_production(self) -> bool:
        # Na Vercel (VERCEL=1) vale como produção mesmo se ENVIRONMENT for esquecida ou escrita
        # como "Production" — as travas abaixo não podem depender de digitar certo.
        return self.ENVIRONMENT.strip().lower() == "production" or os.environ.get("VERCEL") == "1"

    @model_validator(mode="after")
    def _validate_production_settings(self) -> "Settings":
        if not self.is_production:
            return self
        if self.SECRET_KEY in _INSECURE_SECRET_KEYS or len(self.SECRET_KEY) < 32:
            raise ValueError(
                "SECRET_KEY precisa ser aleatória e ter pelo menos 32 caracteres em produção."
            )
        if self.DATABASE_URL.startswith("sqlite"):
            # Sem DATABASE_URL a API cairia no SQLite padrão, num disco somente leitura: todo
            # endpoint com banco daria 500 enquanto o /health continuaria "ok".
            raise ValueError("DATABASE_URL não configurada: produção exige Postgres, não SQLite.")
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    # O .env padrão é só para o dev local (SQLite). Comandos pontuais contra o Neon usam um
    # arquivo separado, escolhido explicitamente: NEXFI_ENV_FILE=.env.neon alembic upgrade head
    # Na Vercel nenhum dos dois existe — as variáveis vêm do ambiente do projeto.
    return Settings(_env_file=os.environ.get("NEXFI_ENV_FILE", ".env"))


settings = get_settings()
