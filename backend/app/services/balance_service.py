import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.models.transfer import Transfer
from app.utils.money import to_decimal
from app.utils.dates import local_today

DEBIT_TYPES = {
    TransactionType.DESPESA,
    TransactionType.PAGAMENTO_FATURA,
    TransactionType.PAGAMENTO_FINANCIAMENTO,
    TransactionType.AMORTIZACAO,
}
CREDIT_TYPES = {TransactionType.RECEITA, TransactionType.RENDIMENTO}


def _signed_contribution(txn: Transaction, account_id: uuid.UUID, transfers_by_id: dict) -> Decimal:
    amount = to_decimal(txn.amount)
    if txn.type in CREDIT_TYPES:
        return amount
    if txn.type in DEBIT_TYPES:
        return -amount
    if txn.type == TransactionType.AJUSTE:
        # O valor do ajuste já é a diferença assinada (pode ser negativa).
        return amount
    if txn.type == TransactionType.TRANSFERENCIA:
        transfer = transfers_by_id.get(txn.transfer_id)
        if transfer is None:
            return Decimal("0")
        if transfer.from_account_id == account_id:
            return -amount
        return amount
    return Decimal("0")


def get_account_balance(db: Session, account: Account) -> Decimal:
    stmt = select(Transaction).where(
        Transaction.account_id == account.id,
        Transaction.status == TransactionStatus.CONFIRMADA,
        Transaction.deleted_at.is_(None),
    )
    transactions = list(db.scalars(stmt))
    transfer_ids = {t.transfer_id for t in transactions if t.transfer_id is not None}
    transfers_by_id = {}
    if transfer_ids:
        transfers_by_id = {
            t.id: t for t in db.scalars(select(Transfer).where(Transfer.id.in_(transfer_ids)))
        }
    total = to_decimal(account.initial_balance)
    for txn in transactions:
        total += _signed_contribution(txn, account.id, transfers_by_id)
    return total


def get_projected_balance(db: Session, account: Account, horizon_days: int = 30) -> Decimal:
    """Saldo atual + receitas/despesas PENDENTES dentro do horizonte informado."""
    from datetime import date, timedelta

    current = get_account_balance(db, account)
    limit_date = local_today() + timedelta(days=horizon_days)
    stmt = select(Transaction).where(
        Transaction.account_id == account.id,
        Transaction.status == TransactionStatus.PENDENTE,
        Transaction.deleted_at.is_(None),
        Transaction.competence_date <= limit_date,
    )
    pending = list(db.scalars(stmt))
    total = current
    for txn in pending:
        amount = to_decimal(txn.amount)
        if txn.type in CREDIT_TYPES:
            total += amount
        elif txn.type in DEBIT_TYPES:
            total -= amount
    return total
