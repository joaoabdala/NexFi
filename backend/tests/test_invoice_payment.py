from datetime import date
from decimal import Decimal

from app.models.enums import InvoiceStatus
from app.schemas.card import CreditCardCreate, CreditCardPurchaseCreate, InvoicePayRequest
from app.services.balance_service import get_account_balance
from app.services.card_service import create_card
from app.services.dashboard_service import get_summary
from app.services.invoice_service import compute_invoice_amount, list_invoices, pay_invoice
from app.services.purchase_service import create_purchase


def test_invoice_payment_does_not_duplicate_expense(db, account, institution, expense_category):
    card = create_card(
        db,
        account.user_id,
        CreditCardCreate(
            institution_id=institution.id,
            name="Cartão Teste",
            credit_limit=Decimal("3000.00"),
            closing_day=5,
            due_day=12,
            default_payment_account_id=account.id,
        ),
    )

    create_purchase(
        db,
        account.user_id,
        card["id"],
        CreditCardPurchaseCreate(
            description="Restaurante",
            total_amount=Decimal("200.00"),
            installments_total=1,
            purchase_date=date.today(),
            category_id=expense_category.id,
        ),
    )

    summary_before = get_summary(db, account.user_id)
    balance_before = get_account_balance(db, account)

    invoices = list_invoices(db, account.user_id, card["id"])
    invoice = invoices[0]
    amount = compute_invoice_amount(db, invoice)
    assert amount == Decimal("200.00")

    pay_invoice(db, account.user_id, invoice.id, date.today(), account.id)

    summary_after = get_summary(db, account.user_id)
    balance_after = get_account_balance(db, account)

    # A despesa já foi contabilizada na compra — o pagamento da fatura não pode
    # somar novamente ao total de despesas do período (§22/§69, critério de aceite §67).
    assert summary_after["expenses_month"] == summary_before["expenses_month"]
    # Mas o caixa da conta deve refletir a saída do pagamento.
    assert balance_before - balance_after == Decimal("200.00")


def test_paid_invoice_cannot_be_paid_twice(db, account, institution, expense_category):
    card = create_card(
        db,
        account.user_id,
        CreditCardCreate(
            institution_id=institution.id,
            name="Cartão Teste",
            credit_limit=Decimal("3000.00"),
            closing_day=5,
            due_day=12,
            default_payment_account_id=account.id,
        ),
    )
    create_purchase(
        db,
        account.user_id,
        card["id"],
        CreditCardPurchaseCreate(
            description="Mercado",
            total_amount=Decimal("100.00"),
            installments_total=1,
            purchase_date=date.today(),
            category_id=expense_category.id,
        ),
    )
    invoice = list_invoices(db, account.user_id, card["id"])[0]
    pay_invoice(db, account.user_id, invoice.id, date.today(), account.id)

    import pytest

    from app.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        pay_invoice(db, account.user_id, invoice.id, date.today(), account.id)
