from collections.abc import Generator

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise UnauthorizedError("Não autenticado.")
    user_id = decode_access_token(token)
    if not user_id:
        raise UnauthorizedError("Token inválido ou expirado.")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise UnauthorizedError("Usuário inválido.")
    return user


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError("Apenas administradores podem acessar este recurso.")
    return current_user


CurrentUser = Depends(get_current_user)
CurrentAdminUser = Depends(get_current_admin_user)
DbSession = Depends(get_db)
