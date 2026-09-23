from decimal import Decimal

from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.schemas.card import CreditCardCreate, CreditCardPurchaseCreate
from app.services.card_service import create_card
from app.services.invoice_service import get_invoice_projection, list_invoices, pay_invoice
from app.services.purchase_service import create_purchase
from app.utils.dates import local_today


def _card(db, user, account, institution, name):
    return create_card(
        db, user.id,
        CreditCardCreate(institution_id=institution.id, name=name, credit_limit=Decimal("9000.00"),
                         closing_day=1, due_day=10, default_payment_account_id=account.id),
    )


def _buy(db, user, card, total, installments, category):
    create_purchase(
        db, user.id, card["id"],
        CreditCardPurchaseCreate(description="Compra", total_amount=Decimal(total), installments_total=installments,
                                 purchase_date=local_today(), category_id=category.id),
    )


def test_installments_land_in_their_due_months_per_card(db, user, account, institution, expense_category):
    nubank = _card(db, user, account, institution, "Nubank")
    itau = _card(db, user, account, institution, "Itaú")
    _buy(db, user, nubank, "300.00", 3, expense_category)  # 3 x 100
    _buy(db, user, itau, "50.00", 1, expense_category)

    projection = get_invoice_projection(db, user.id, months=12)

    assert [c["name"] for c in projection["cards"]] == ["Itaú", "Nubank"]  # ordem estável por nome
    assert len(projection["months"]) == 12
    with_amount = [m for m in projection["months"] if m["total"] > 0]
    assert [m["by_card"].get(str(nubank["id"])) for m in with_amount] == [Decimal("100.00")] * 3
    assert with_amount[0]["total"] == Decimal("150.00")  # 100 do Nubank + 50 do Itaú no 1º vencimento
    assert sum(m["total"] for m in projection["months"]) == Decimal("350.00")


def test_paid_invoice_is_not_projected(db, user, account, institution, expense_category):
    card = _card(db, user, account, institution, "Cartão")
    _buy(db, user, card, "80.00", 1, expense_category)
    pay_invoice(db, user.id, list_invoices(db, user.id, card["id"])[0].id, local_today(), account.id)

    projection = get_invoice_projection(db, user.id, months=12)
    assert all(m["total"] == 0 for m in projection["months"])
    assert projection["cards"] == []


def test_route_is_not_confused_with_card_id(db, user):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        response = TestClient(app).get("/api/v1/cards/invoice-projection?months=6")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert len(response.json()["months"]) == 6
