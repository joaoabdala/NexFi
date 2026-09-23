import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.institution import FinancialInstitution


def list_by_user(db: Session, user_id: uuid.UUID) -> list[FinancialInstitution]:
    stmt = select(FinancialInstitution).where(FinancialInstitution.user_id == user_id).order_by(
        FinancialInstitution.name
    )
    return list(db.scalars(stmt))


def get_by_id(db: Session, user_id: uuid.UUID, institution_id: uuid.UUID) -> FinancialInstitution | None:
    stmt = select(FinancialInstitution).where(
        FinancialInstitution.id == institution_id, FinancialInstitution.user_id == user_id
    )
    return db.scalar(stmt)
