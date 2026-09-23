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


PG_URL = "postgresql://u:p@ep-x-pooler.sa-east-1.aws.neon.tech/neondb"


@pytest.fixture(autouse=True)
def _not_on_vercel(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)


def test_production_refuses_default_secret_key():
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None, ENVIRONMENT="production", DATABASE_URL=PG_URL)


@pytest.mark.parametrize("key", ["", "curta", "x" * 31])
def test_production_refuses_short_secret_key(key):
    """python-jose/PyJWT assinam até com chave vazia — o tamanho mínimo precisa ser checado."""
    with pytest.raises(ValidationError, match="32 caracteres"):
        Settings(_env_file=None, ENVIRONMENT="production", DATABASE_URL=PG_URL, SECRET_KEY=key)


def test_production_refuses_sqlite_fallback():
    """Sem DATABASE_URL na Vercel, a API cairia no SQLite (disco somente leitura)."""
    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings(_env_file=None, ENVIRONMENT="production", SECRET_KEY="x" * 64)


@pytest.mark.parametrize("env", ["Production", " PRODUCTION "])
def test_environment_is_case_insensitive(env):
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None, ENVIRONMENT=env, DATABASE_URL=PG_URL)


def test_vercel_counts_as_production_even_without_environment(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None, ENVIRONMENT="development", DATABASE_URL=PG_URL)


def test_production_accepts_real_configuration():
    settings = Settings(_env_file=None, ENVIRONMENT="production", SECRET_KEY="x" * 64, DATABASE_URL=PG_URL)
    assert settings.is_production
