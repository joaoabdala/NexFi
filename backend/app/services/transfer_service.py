import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.models.transfer import Transfer
from app.repositories import account_repository
from app.schemas.transfer import TransferCreate


def list_transfers(db: Session, user_id: uuid.UUID) -> list[Transfer]:
    stmt = select(Transfer).where(Transfer.user_id == user_id).order_by(Transfer.date.desc())
    return list(db.scalars(stmt))


def get_transfer(db: Session, user_id: uuid.UUID, transfer_id: uuid.UUID) -> Transfer:
    stmt = select(Transfer).where(Transfer.id == transfer_id, Transfer.user_id == user_id)
    transfer = db.scalar(stmt)
    if not transfer:
        raise NotFoundError("Transferência não encontrada.")
    return transfer


def create_transfer(db: Session, user_id: uuid.UUID, payload: TransferCreate) -> Transfer:
    if payload.from_account_id == payload.to_account_id:
        raise ValidationError("A conta de origem deve ser diferente da conta de destino.")

    from_account = account_repository.get_by_id(db, user_id, payload.from_account_id)
    to_account = account_repository.get_by_id(db, user_id, payload.to_account_id)
    if not from_account or not to_account:
        raise ValidationError("Conta de origem ou destino inválida.")
    if not from_account.active or not to_account.active:
        raise ValidationError("Não é possível transferir usando uma conta inativa.")

    description = payload.description or f"Transferência: {from_account.name} → {to_account.name}"

    try:
        transfer = Transfer(
            user_id=user_id,
            from_account_id=payload.from_account_id,
            to_account_id=payload.to_account_id,
            amount=payload.amount,
            date=payload.date,
            description=description,
            note=payload.note,
        )
        db.add(transfer)
        db.flush()

        outgoing = Transaction(
            user_id=user_id,
            account_id=from_account.id,
            category_id=None,
            description=description,
            type=TransactionType.TRANSFERENCIA,
            amount=payload.amount,
            competence_date=payload.date,
            payment_date=payload.date,
            status=TransactionStatus.CONFIRMADA,
            origin="TRANSFERENCIA",
            transfer_id=transfer.id,
        )
        incoming = Transaction(
            user_id=user_id,
            account_id=to_account.id,
            category_id=None,
            description=description,
            type=TransactionType.TRANSFERENCIA,
            amount=payload.amount,
            competence_date=payload.date,
            payment_date=payload.date,
            status=TransactionStatus.CONFIRMADA,
            origin="TRANSFERENCIA",
            transfer_id=transfer.id,
        )
        db.add_all([outgoing, incoming])
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(transfer)
    return transfer


def cancel_transfer(db: Session, user_id: uuid.UUID, transfer_id: uuid.UUID) -> Transfer:
    """Desfaz uma transferência: os dois lançamentos (saída e entrada) ficam CANCELADOS e os
    saldos das duas contas voltam ao que eram. O registro continua no histórico."""
    transfer = get_transfer(db, user_id, transfer_id)
    legs = list(
        db.scalars(
            select(Transaction).where(
                Transaction.transfer_id == transfer.id,
                Transaction.user_id == user_id,
                Transaction.status == TransactionStatus.CONFIRMADA,
            )
        )
    )
    if not legs:
        raise ValidationError("Esta transferência já foi desfeita.")
    for leg in legs:
        leg.status = TransactionStatus.CANCELADA
        db.add(leg)
    db.commit()
    db.refresh(transfer)
    return transfer
