import pytest
from sqlalchemy.engine import make_url

from app.core.config import get_settings
from app.seeds.seed import ensure_local_database


@pytest.mark.parametrize(
    "url",
    [
        "sqlite:///./dev.db",
        "sqlite:///:memory:",
        "postgresql+psycopg://nexfi:nexfi@localhost:5432/nexfi",
        "postgresql+psycopg://nexfi:nexfi@127.0.0.1/nexfi",
    ],
)
def test_seed_allows_local_databases(url):
    ensure_local_database(make_url(url))


def test_seed_refuses_remote_database():
    """Rodar o seed no Neon criaria um ADMIN demo@abdalanexus.com / demo123 em produção."""
    url = make_url("postgresql+psycopg://u:p@ep-x-pooler.sa-east-1.aws.neon.tech/neondb")
    with pytest.raises(SystemExit, match="não é local"):
        ensure_local_database(url)


def test_env_file_can_be_chosen_explicitly(tmp_path, monkeypatch):
    """Comandos contra o Neon usam NEXFI_ENV_FILE=.env.neon; o .env padrão fica só no SQLite."""
    custom = tmp_path / ".env.neon"
    custom.write_text("DATABASE_URL=postgresql://u:p@host.example/db\n", encoding="utf-8")
    monkeypatch.setenv("NEXFI_ENV_FILE", str(custom))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()
    try:
        assert get_settings().DATABASE_URL == "postgresql+psycopg://u:p@host.example/db"
    finally:
        get_settings.cache_clear()
