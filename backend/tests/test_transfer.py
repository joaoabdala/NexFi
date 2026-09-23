from datetime import date
from decimal import Decimal

import pytest

from app.core.exceptions import ValidationError
from app.schemas.transfer import TransferCreate
from app.services.balance_service import get_account_balance
from app.services.dashboard_service import get_summary
from app.services.transfer_service import create_transfer


def test_transfer_moves_money_between_accounts_without_income_or_expense(db, account, account2):
    create_transfer(
        db,
        account.user_id,
        TransferCreate(
            from_account_id=account.id,
            to_account_id=account2.id,
            amount=Decimal("300.00"),
            date=date(2026, 2, 1),
        ),
    )

    assert get_account_balance(db, account) == Decimal("700.00")
    assert get_account_balance(db, account2) == Decimal("800.00")

    summary = get_summary(db, account.user_id)
    assert summary["income_month"] == Decimal("0.00")
    assert summary["expenses_month"] == Decimal("0.00")


def test_transfer_total_worth_unchanged(db, account, account2):
    before = get_account_balance(db, account) + get_account_balance(db, account2)
    create_transfer(
        db,
        account.user_id,
        TransferCreate(
            from_account_id=account.id,
            to_account_id=account2.id,
            amount=Decimal("150.00"),
            date=date(2026, 2, 1),
        ),
    )
    after = get_account_balance(db, account) + get_account_balance(db, account2)
    assert before == after


def test_transfer_rejects_same_account(db, account):
    with pytest.raises(ValidationError):
        create_transfer(
            db,
            account.user_id,
            TransferCreate(
                from_account_id=account.id,
                to_account_id=account.id,
                amount=Decimal("10.00"),
                date=date(2026, 2, 1),
            ),
        )
