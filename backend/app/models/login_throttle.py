from datetime import datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import TZDateTime


class LoginThrottle(Base):
    """Contador de falhas de login por chave ("email:<e-mail>" ou "ip:<endereço>").

    Fica no banco porque na Vercel cada requisição pode cair numa instância diferente da função
    — um contador em memória não barraria ataque de força bruta.
    """

    __tablename__ = "login_throttles"

    key: Mapped[str] = mapped_column(String(320), primary_key=True)
    failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    window_started_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(TZDateTime, nullable=True)
