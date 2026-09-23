import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.budget import Budget


def list_by_user(db: Session, user_id: uuid.UUID) -> list[Budget]:
    stmt = select(Budget).where(Budget.user_id == user_id)
    return list(db.scalars(stmt))


def get_by_id(db: Session, user_id: uuid.UUID, budget_id: uuid.UUID) -> Budget | None:
    stmt = select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
    return db.scalar(stmt)


def get_scoped(
    db: Session, user_id: uuid.UUID, category_id: uuid.UUID, month: int | None, year: int | None
) -> Budget | None:
    stmt = select(Budget).where(
        Budget.user_id == user_id,
        Budget.category_id == category_id,
        Budget.month == month,
        Budget.year == year,
    )
    return db.scalar(stmt)
