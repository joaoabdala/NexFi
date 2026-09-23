import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.recurrence import RecurrenceRule


def list_by_user(db: Session, user_id: uuid.UUID) -> list[RecurrenceRule]:
    stmt = select(RecurrenceRule).where(RecurrenceRule.user_id == user_id).order_by(
        RecurrenceRule.description
    )
    return list(db.scalars(stmt))


def get_by_id(db: Session, user_id: uuid.UUID, rule_id: uuid.UUID) -> RecurrenceRule | None:
    stmt = select(RecurrenceRule).where(RecurrenceRule.id == rule_id, RecurrenceRule.user_id == user_id)
    return db.scalar(stmt)


def list_active(db: Session, user_id: uuid.UUID) -> list[RecurrenceRule]:
    stmt = select(RecurrenceRule).where(
        RecurrenceRule.user_id == user_id, RecurrenceRule.active.is_(True)
    )
    return list(db.scalars(stmt))
