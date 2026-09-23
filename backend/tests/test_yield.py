from datetime import date
from decimal import Decimal

from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.services.balance_service import get_account_balance
from app.services.dashboard_service import get_summary


def test_yield_increases_balance_and_worth_but_not_income(db, account):
    today = date.today()
    db.add(
        Transaction(
            user_id=account.user_id,
            account_id=account.id,
            category_id=None,
            description="Rendimento cofrinho",
            type=TransactionType.RENDIMENTO,
            amount=Decimal("22.40"),
            competence_date=today,
            payment_date=today,
            status=TransactionStatus.CONFIRMADA,
            origin="MANUAL",
        )
    )
    db.commit()

    assert get_account_balance(db, account) == Decimal("1022.40")

    summary = get_summary(db, account.user_id)
    assert summary["income_month"] == Decimal("0.00")
    assert summary["yield_month"] == Decimal("22.40")
