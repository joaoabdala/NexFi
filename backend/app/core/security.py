import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

# bcrypt só considera os primeiros 72 bytes da senha (e o bcrypt 5 recusa senhas maiores).
# Os schemas limitam o tamanho; aqui é a última barreira.
BCRYPT_MAX_BYTES = 72

# Hash fixo usado quando o e-mail não existe, para o login levar o mesmo tempo nos dois casos
# (sem isso, a resposta instantânea revelava quais e-mails têm conta).
_DUMMY_HASH = bcrypt.hashpw(b"nexfi-dummy-password", bcrypt.gensalt()).decode()


def hash_password(password: str) -> str:
    encoded = password.encode()
    if len(encoded) > BCRYPT_MAX_BYTES:
        raise ValueError("Senha maior que 72 bytes.")
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode()


def verify_password(plain_password: str, password_hash: str | None) -> bool:
    """Compara em tempo constante. Com ``password_hash=None`` (usuário inexistente) ainda roda um
    bcrypt completo contra um hash fixo e devolve False."""
    encoded = plain_password.encode()[:BCRYPT_MAX_BYTES]
    try:
        matches = bcrypt.checkpw(encoded, (password_hash or _DUMMY_HASH).encode())
    except ValueError:  # hash corrompido/formato desconhecido
        return False
    return matches and password_hash is not None


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {"sub": subject, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError:
        return None
    if payload.get("type") != "access":
        return None
    return payload.get("sub")


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    # SHA-256 é suficiente aqui: o token bruto já possui alta entropia (secrets.token_urlsafe),
    # diferente de senhas de usuário que exigem bcrypt por serem de baixa entropia.
    import hashlib

    return hashlib.sha256(token.encode()).hexdigest()
