import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category


def list_by_user(db: Session, user_id: uuid.UUID) -> list[Category]:
    stmt = select(Category).where(Category.user_id == user_id).order_by(Category.name)
    return list(db.scalars(stmt))


def get_by_id(db: Session, user_id: uuid.UUID, category_id: uuid.UUID) -> Category | None:
    stmt = select(Category).where(Category.id == category_id, Category.user_id == user_id)
    return db.scalar(stmt)
