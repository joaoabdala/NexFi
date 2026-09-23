import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories import user_repository
from app.schemas.admin import AdminUserCreate, AdminUserUpdate


def list_users(db: Session) -> list[User]:
    return user_repository.list_all(db)


def get_user(db: Session, user_id: uuid.UUID) -> User:
    user = user_repository.get_by_id(db, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado.")
    return user


def create_user(db: Session, payload: AdminUserCreate) -> User:
    if user_repository.get_by_email(db, payload.email):
        raise ConflictError("Já existe um usuário com este e-mail.")

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        name=payload.name,
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _ensure_at_least_one_active_admin_remains(db: Session, target: User, payload: AdminUserUpdate) -> None:
    """Impede que a última conta de administrador ativa seja rebaixada ou desativada."""
    is_admin = target.role == UserRole.ADMIN and target.is_active
    would_stay_admin = (
        (payload.role if payload.role is not None else target.role) == UserRole.ADMIN
        and (payload.is_active if payload.is_active is not None else target.is_active)
    )
    if is_admin and not would_stay_admin:
        remaining = user_repository.count_active_admins(db, exclude_user_id=target.id)
        if remaining < 1:
            raise ValidationError(
                "Não é possível remover o último administrador ativo do sistema."
            )


def update_user(db: Session, user_id: uuid.UUID, payload: AdminUserUpdate) -> User:
    user = get_user(db, user_id)
    data = payload.model_dump(exclude_unset=True, exclude={"password"})

    if "email" in data and data["email"] is not None:
        data["email"] = data["email"].lower()
        existing = user_repository.get_by_email(db, data["email"])
        if existing and existing.id != user.id:
            raise ConflictError("Já existe um usuário com este e-mail.")

    _ensure_at_least_one_active_admin_remains(db, user, payload)

    for field, value in data.items():
        setattr(user, field, value)
    if payload.password:
        user.password_hash = hash_password(payload.password)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, requesting_user: User, user_id: uuid.UUID) -> None:
    if requesting_user.id == user_id:
        raise ValidationError("Você não pode excluir a própria conta.")

    user = get_user(db, user_id)
    if user.role == UserRole.ADMIN and user.is_active:
        remaining = user_repository.count_active_admins(db, exclude_user_id=user.id)
        if remaining < 1:
            raise ValidationError("Não é possível excluir o último administrador ativo do sistema.")

    # Exclusão em cascata: todas as instituições, contas, transações, cartões,
    # financiamentos etc. do usuário são removidos junto (ON DELETE CASCADE no banco).
    db.delete(user)
    db.commit()
