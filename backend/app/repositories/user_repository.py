import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User


def list_all(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.name)))


def get_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def count_active_admins(db: Session, exclude_user_id: uuid.UUID | None = None) -> int:
    stmt = select(func.count()).select_from(User).where(
        User.role == UserRole.ADMIN, User.is_active.is_(True)
    )
    if exclude_user_id:
        stmt = stmt.where(User.id != exclude_user_id)
    return db.scalar(stmt) or 0
