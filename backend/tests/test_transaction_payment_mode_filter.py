from datetime import date
from decimal import Decimal

from app.repositories import transaction_repository
from app.schemas.card import CreditCardCreate, CreditCardPurchaseCreate
from app.schemas.transaction import TransactionFilters
from app.services.card_service import create_card
from app.services.purchase_service import create_purchase


def test_payment_mode_filter_separates_avista_from_parcelado(db, account, institution, expense_category):
    card = create_card(
        db,
        account.user_id,
        CreditCardCreate(
            institution_id=institution.id,
            name="Cartão Teste",
            credit_limit=Decimal("5000.00"),
            closing_day=10,
            due_day=20,
            default_payment_account_id=account.id,
        ),
    )

    create_purchase(
        db,
        account.user_id,
        card["id"],
        CreditCardPurchaseCreate(
            description="Compra à vista",
            total_amount=Decimal("100.00"),
            installments_total=1,
            purchase_date=date(2026, 3, 1),
            category_id=expense_category.id,
        ),
    )
    create_purchase(
        db,
        account.user_id,
        card["id"],
        CreditCardPurchaseCreate(
            description="Compra parcelada",
            total_amount=Decimal("900.00"),
            installments_total=3,
            purchase_date=date(2026, 3, 1),
            category_id=expense_category.id,
        ),
    )

    parcelado_items, parcelado_total = transaction_repository.search(
        db, account.user_id, TransactionFilters(payment_mode="PARCELADO", page=1, page_size=20)
    )
    assert parcelado_total == 3  # as 3 parcelas da compra parcelada
    assert all("parcelada" in i.description for i in parcelado_items)

    avista_items, avista_total = transaction_repository.search(
        db, account.user_id, TransactionFilters(payment_mode="AVISTA", page=1, page_size=20)
    )
    assert avista_total == 1
    assert avista_items[0].description == "Compra à vista"


def test_regular_manual_transactions_count_as_avista(db, account, expense_category):
    from app.models.enums import TransactionStatus, TransactionType
    from app.models.transaction import Transaction

    db.add(
        Transaction(
            user_id=account.user_id,
            account_id=account.id,
            category_id=expense_category.id,
            description="Supermercado",
            type=TransactionType.DESPESA,
            amount=Decimal("150.00"),
            competence_date=date(2026, 3, 5),
            payment_date=date(2026, 3, 5),
            status=TransactionStatus.CONFIRMADA,
            origin="MANUAL",
        )
    )
    db.commit()

    avista_items, avista_total = transaction_repository.search(
        db, account.user_id, TransactionFilters(payment_mode="AVISTA", page=1, page_size=20)
    )
    assert avista_total == 1
    assert avista_items[0].description == "Supermercado"

    parcelado_items, parcelado_total = transaction_repository.search(
        db, account.user_id, TransactionFilters(payment_mode="PARCELADO", page=1, page_size=20)
    )
    assert parcelado_total == 0
