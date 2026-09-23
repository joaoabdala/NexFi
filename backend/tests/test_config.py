import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://u:p@ep-x-pooler.sa-east-1.aws.neon.tech/nexfi?sslmode=require",
        "postgres://u:p@ep-x-pooler.sa-east-1.aws.neon.tech/nexfi?sslmode=require",
    ],
)
def test_neon_url_is_forced_to_psycopg3_driver(url):
    """A connection string copiada do Neon não traz o driver; sem normalizar, o SQLAlchemy
    tentaria importar psycopg2 e a API nem subiria na Vercel."""
    settings = Settings(_env_file=None, DATABASE_URL=url)
    assert settings.DATABASE_URL.startswith("postgresql+psycopg://u:p@ep-x-pooler")
    assert settings.DATABASE_URL.endswith("?sslmode=require")


def test_explicit_driver_and_sqlite_urls_are_untouched():
    for url in ("postgresql+psycopg://u:p@h/db", "sqlite:///./dev.db"):
        assert Settings(_env_file=None, DATABASE_URL=url).DATABASE_URL == url


def test_production_refuses_default_secret_key():
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None, ENVIRONMENT="production")


def test_production_accepts_real_secret_key():
    settings = Settings(_env_file=None, ENVIRONMENT="production", SECRET_KEY="x" * 64)
    assert settings.ENVIRONMENT == "production"
