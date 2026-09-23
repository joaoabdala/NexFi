"""Limite de tentativas de login (força bruta), por e-mail e por IP."""

import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, or_
from sqlalchemy.orm import Session

from app.core.exceptions import TooManyRequestsError
from app.models.login_throttle import LoginThrottle

WINDOW = timedelta(minutes=15)
LOCKOUT = timedelta(minutes=15)
# Por e-mail: protege uma conta específica. Por IP: barra quem testa muitas contas de uma vez
# (mais folgado, porque vários usuários legítimos podem sair pelo mesmo IP).
MAX_FAILURES_PER_EMAIL = 5
MAX_FAILURES_PER_IP = 20


def _keys(email: str, ip: str | None) -> list[tuple[str, int]]:
    keys = [(f"email:{email.strip().lower()}", MAX_FAILURES_PER_EMAIL)]
    if ip:
        keys.append((f"ip:{ip}", MAX_FAILURES_PER_IP))
    return keys


def ensure_not_locked(db: Session, email: str, ip: str | None) -> None:
    now = datetime.now(timezone.utc)
    for key, _ in _keys(email, ip):
        row = db.get(LoginThrottle, key)
        if row and row.locked_until and row.locked_until > now:
            minutes = max(1, math.ceil((row.locked_until - now).total_seconds() / 60))
            raise TooManyRequestsError(
                f"Muitas tentativas de login. Tente novamente em {minutes} minuto(s)."
            )


def register_failure(db: Session, email: str, ip: str | None) -> None:
    now = datetime.now(timezone.utc)
    for key, limit in _keys(email, ip):
        row = db.get(LoginThrottle, key)
        if row is None:
            row = LoginThrottle(key=key, failures=0, window_started_at=now)
            db.add(row)
        elif now - row.window_started_at > WINDOW:
            row.failures, row.window_started_at, row.locked_until = 0, now, None
        row.failures += 1
        if row.failures >= limit:
            row.locked_until = now + LOCKOUT
    # Faxina: contadores antigos e sem bloqueio ativo não servem mais para nada.
    stale = now - timedelta(days=1)
    db.execute(
        delete(LoginThrottle).where(
            LoginThrottle.window_started_at < stale,
            or_(LoginThrottle.locked_until.is_(None), LoginThrottle.locked_until < now),
        )
    )
    db.commit()


def register_success(db: Session, email: str) -> None:
    db.execute(delete(LoginThrottle).where(LoginThrottle.key == f"email:{email.strip().lower()}"))
    db.commit()
