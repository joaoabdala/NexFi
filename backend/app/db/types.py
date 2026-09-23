import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import CHAR, DateTime, TypeDecorator


class GUID(TypeDecorator):
    """Tipo UUID portável: nativo no PostgreSQL, CHAR(32) hexadecimal no SQLite.

    Permite rodar migrations e testes sem depender de um Postgres real,
    mantendo Postgres como banco de produção documentado.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(str(value))
        return value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)
        return value


class TZDateTime(TypeDecorator):
    """DateTime timezone-aware portável entre dialetos.

    SQLite não preserva `tzinfo` ao ler de volta um `DateTime(timezone=True)` — o valor
    retorna *naive*, o que quebra qualquer comparação com um `datetime` aware (ex.:
    `expires_at < datetime.now(timezone.utc)` para checar expiração de um refresh token,
    que sem isso levanta `TypeError: can't compare offset-naive and offset-aware
    datetimes` e derruba o endpoint). Este tipo sempre grava em UTC e sempre devolve um
    valor com `tzinfo=UTC` anexado, no PostgreSQL ou no SQLite.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return value
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return value
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
