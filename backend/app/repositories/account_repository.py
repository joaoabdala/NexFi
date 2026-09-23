import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account


def list_by_user(db: Session, user_id: uuid.UUID, active_only: bool = False) -> list[Account]:
    stmt = select(Account).where(Account.user_id == user_id, Account.deleted_at.is_(None))
    if active_only:
        stmt = stmt.where(Account.active.is_(True))
    return list(db.scalars(stmt.order_by(Account.name)))


def get_by_id(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> Account | None:
    stmt = select(Account).where(
        Account.id == account_id, Account.user_id == user_id, Account.deleted_at.is_(None)
    )
    return db.scalar(stmt)
