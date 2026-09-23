import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.financing import Amortization, CommitmentInstallment, FinancialCommitment


def list_commitments(db: Session, user_id: uuid.UUID) -> list[FinancialCommitment]:
    stmt = (
        select(FinancialCommitment)
        .where(FinancialCommitment.user_id == user_id)
        .order_by(FinancialCommitment.start_date.desc())
    )
    return list(db.scalars(stmt))


def get_commitment(db: Session, user_id: uuid.UUID, commitment_id: uuid.UUID) -> FinancialCommitment | None:
    stmt = select(FinancialCommitment).where(
        FinancialCommitment.id == commitment_id, FinancialCommitment.user_id == user_id
    )
    return db.scalar(stmt)


def list_installments(db: Session, commitment_id: uuid.UUID) -> list[CommitmentInstallment]:
    stmt = (
        select(CommitmentInstallment)
        .where(CommitmentInstallment.commitment_id == commitment_id)
        .order_by(CommitmentInstallment.number)
    )
    return list(db.scalars(stmt))


def get_installment(
    db: Session, commitment_id: uuid.UUID, installment_id: uuid.UUID
) -> CommitmentInstallment | None:
    stmt = select(CommitmentInstallment).where(
        CommitmentInstallment.id == installment_id,
        CommitmentInstallment.commitment_id == commitment_id,
    )
    return db.scalar(stmt)


def list_amortizations(db: Session, commitment_id: uuid.UUID) -> list[Amortization]:
    stmt = (
        select(Amortization)
        .where(Amortization.commitment_id == commitment_id)
        .order_by(Amortization.date.desc())
    )
    return list(db.scalars(stmt))
