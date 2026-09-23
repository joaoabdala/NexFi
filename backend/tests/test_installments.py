from datetime import date
from decimal import Decimal

from app.repositories import card_repository
from app.schemas.card import CreditCardCreate, CreditCardPurchaseCreate
from app.services.card_service import create_card
from app.services.purchase_service import create_purchase, purchase_metrics


def test_installment_purchase_splits_across_invoices_without_rounding_loss(
    db, account, institution, expense_category
):
    card = create_card(
        db,
        account.user_id,
        CreditCardCreate(
            institution_id=institution.id,
            name="Cartão Teste",
            credit_limit=Decimal("10000.00"),
            closing_day=10,
            due_day=20,
            default_payment_account_id=account.id,
        ),
    )

    purchase = create_purchase(
        db,
        account.user_id,
        card["id"],
        CreditCardPurchaseCreate(
            description="Notebook",
            total_amount=Decimal("1000.00"),
            installments_total=3,
            purchase_date=date(2026, 3, 1),
            category_id=expense_category.id,
        ),
    )

    installments = card_repository.list_installments_by_purchase(db, purchase.id)
    assert len(installments) == 3
    amounts = [i.amount for i in installments]
    # 1000 / 3 não é exato — o resíduo de centavos deve ir para a última parcela,
    # e a soma das parcelas deve bater exatamente com o valor total da compra.
    assert sum(amounts) == Decimal("1000.00")
    assert amounts[0] == amounts[1] == Decimal("333.33")
    assert amounts[2] == Decimal("333.34")

    # Cada parcela cai em uma competência (fatura) distinta e sequencial.
    competences = [i.invoice.competence for i in installments]
    assert competences == sorted(competences)
    assert len(set(competences)) == 3

    metrics = purchase_metrics(db, purchase)
    assert metrics["installments_remaining"] == 3
    assert metrics["future_amount"] == Decimal("1000.00")
    assert metrics["invoiced_amount"] == Decimal("0.00")
