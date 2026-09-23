from datetime import date
from decimal import Decimal

from app.models.category import Category
from app.models.enums import CategoryKind, TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.schemas.budget import BudgetCreate
from app.services.budget_service import create_budget, get_summary


def test_budget_summary_computes_realized_remaining_and_percentage(db, account, expense_category):
    create_budget(
        db,
        account.user_id,
        BudgetCreate(category_id=expense_category.id, amount=Decimal("1200.00")),
    )

    today = date.today()
    db.add(
        Transaction(
            user_id=account.user_id,
            account_id=account.id,
            category_id=expense_category.id,
            description="Mercado",
            type=TransactionType.DESPESA,
            amount=Decimal("300.00"),
            competence_date=today,
            payment_date=today,
            status=TransactionStatus.CONFIRMADA,
            origin="MANUAL",
        )
    )
    db.commit()

    summary = get_summary(db, account.user_id, today.year, today.month)
    assert len(summary) == 1
    item = summary[0]
    assert item["budget_amount"] == Decimal("1200.00")
    assert item["realized_amount"] == Decimal("300.00")
    assert item["remaining_amount"] == Decimal("900.00")
    assert item["percentage_used"] == Decimal("25.00")


def test_month_specific_budget_overrides_default(db, account, expense_category):
    create_budget(
        db, account.user_id, BudgetCreate(category_id=expense_category.id, amount=Decimal("500.00"))
    )
    create_budget(
        db,
        account.user_id,
        BudgetCreate(category_id=expense_category.id, amount=Decimal("1500.00"), month=12, year=2026),
    )

    december = get_summary(db, account.user_id, 2026, 12)
    other_month = get_summary(db, account.user_id, 2026, 6)

    assert december[0]["budget_amount"] == Decimal("1500.00")
    assert other_month[0]["budget_amount"] == Decimal("500.00")


def test_budget_realized_amount_includes_subcategory_transactions(db, account, expense_category):
    """Orçamento na categoria-pai deve somar lançamentos feitos em suas subcategorias."""
    subcategory = Category(
        user_id=account.user_id,
        name="Mercado",
        kind=CategoryKind.DESPESA,
        parent_id=expense_category.id,
    )
    db.add(subcategory)
    db.commit()
    db.refresh(subcategory)

    create_budget(
        db, account.user_id, BudgetCreate(category_id=expense_category.id, amount=Decimal("1000.00"))
    )

    today = date.today()
    db.add(
        Transaction(
            user_id=account.user_id,
            account_id=account.id,
            category_id=subcategory.id,
            description="Supermercado",
            type=TransactionType.DESPESA,
            amount=Decimal("250.00"),
            competence_date=today,
            payment_date=today,
            status=TransactionStatus.CONFIRMADA,
            origin="MANUAL",
        )
    )
    db.commit()

    summary = get_summary(db, account.user_id, today.year, today.month)
    assert summary[0]["realized_amount"] == Decimal("250.00")
