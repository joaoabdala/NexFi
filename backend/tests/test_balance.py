from datetime import date
from decimal import Decimal

from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.schemas.account import BalanceAdjustmentCreate
from app.services.account_service import create_balance_adjustment
from app.services.balance_service import get_account_balance


def test_initial_balance_is_not_income(db, account):
    """Saldo inicial não deve aparecer como receita — apenas ponto de partida (§10)."""
    balance = get_account_balance(db, account)
    assert balance == Decimal("1000.00")


def test_balance_reflects_confirmed_movements_only(db, account, expense_category):
    db.add(
        Transaction(
            user_id=account.user_id,
            account_id=account.id,
            category_id=expense_category.id,
            description="Despesa confirmada",
            type=TransactionType.DESPESA,
            amount=Decimal("300.00"),
            competence_date=date(2026, 2, 1),
            payment_date=date(2026, 2, 1),
            status=TransactionStatus.CONFIRMADA,
            origin="MANUAL",
        )
    )
    db.add(
        Transaction(
            user_id=account.user_id,
            account_id=account.id,
            category_id=expense_category.id,
            description="Despesa pendente (não deve contar)",
            type=TransactionType.DESPESA,
            amount=Decimal("5000.00"),
            competence_date=date(2026, 3, 1),
            payment_date=None,
            status=TransactionStatus.PENDENTE,
            origin="MANUAL",
        )
    )
    db.commit()

    balance = get_account_balance(db, account)
    assert balance == Decimal("700.00")


def test_balance_adjustment_generates_audit_transaction_not_income_or_expense(db, account):
    result = create_balance_adjustment(
        db,
        account.user_id,
        account.id,
        BalanceAdjustmentCreate(informed_balance=Decimal("980.00"), date=date(2026, 2, 10)),
    )
    assert result.difference == Decimal("-20.00")

    balance = get_account_balance(db, account)
    assert balance == Decimal("980.00")

    txn = db.get(Transaction, result.transaction_id)
    assert txn.type == TransactionType.AJUSTE
    assert txn.type not in (TransactionType.RECEITA, TransactionType.DESPESA)
