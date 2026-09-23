from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import UnauthorizedError, ValidationError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.user import User
from app.repositories import auth_repository
from app.schemas.auth import TokenResponse, UpdateProfileRequest


def _issue_tokens(db: Session, user: User) -> TokenResponse:
    access_token = create_access_token(str(user.id))
    refresh_token = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    auth_repository.store_refresh_token(db, user.id, hash_refresh_token(refresh_token), expires_at)
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


def login(db: Session, email: str, password: str) -> TokenResponse:
    user = auth_repository.get_user_by_email(db, email)
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise UnauthorizedError("E-mail ou senha inválidos.")
    return _issue_tokens(db, user)


def refresh(db: Session, refresh_token: str) -> TokenResponse:
    token_hash = hash_refresh_token(refresh_token)
    record = auth_repository.get_refresh_token_by_hash(db, token_hash)
    if not record or record.revoked_at is not None:
        raise UnauthorizedError("Refresh token inválido.")
    if record.expires_at < datetime.now(timezone.utc):
        raise UnauthorizedError("Refresh token expirado.")
    user = db.get(User, record.user_id)
    if not user or not user.is_active:
        raise UnauthorizedError("Usuário inválido.")
    # Rotaciona o refresh token: revoga o atual e emite um novo par.
    auth_repository.revoke_refresh_token(db, record)
    return _issue_tokens(db, user)


def logout(db: Session, refresh_token: str) -> None:
    token_hash = hash_refresh_token(refresh_token)
    record = auth_repository.get_refresh_token_by_hash(db, token_hash)
    if record and record.revoked_at is None:
        auth_repository.revoke_refresh_token(db, record)
        db.commit()


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise ValidationError("Senha atual incorreta.")
    user.password_hash = hash_password(new_password)
    db.add(user)
    db.commit()


def update_profile(db: Session, user: User, payload: UpdateProfileRequest) -> User:
    if payload.name is not None:
        user.name = payload.name
    if payload.timezone is not None:
        user.timezone = payload.timezone
    if payload.locale is not None:
        user.locale = payload.locale
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
