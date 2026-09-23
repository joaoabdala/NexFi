from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if is_sqlite:
    engine_kwargs: dict = {"connect_args": {"check_same_thread": False}}
else:
    engine_kwargs = {
        # Em produção (Vercel + Neon) a conexão passa pelo pooler do Neon (PgBouncer em modo
        # transação), então o pool local fica pequeno e as conexões são recicladas antes de o
        # Neon suspender o compute por inatividade (5 min).
        "pool_size": 5,
        "max_overflow": 5,
        "pool_recycle": 240,
        # Prepared statements automáticos do psycopg 3 não são seguros atrás do PgBouncer em
        # modo transação (a conexão física muda entre transações).
        "connect_args": {"prepare_threshold": None},
    }

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, **engine_kwargs)

if is_sqlite:
    # SQLite não aplica FKs (nem ON DELETE CASCADE) por padrão — sem isso, excluir um
    # usuário deixaria dados financeiros órfãos apenas no ambiente de desenvolvimento.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
