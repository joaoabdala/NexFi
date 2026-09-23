"""Regressões dos bugs de dinheiro e datas encontrados na auditoria pré-deploy."""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import ValidationError
from app.models.enums import AmortizationType, CommitmentStatus, CommitmentType
from app.repositories import financing_repository
from app.schemas.card import CreditCardCreate, CreditCardPurchaseCreate
from app.schemas.financing import (
    AmortizationCreate,
    FinancialCommitmentCreate,
    FinancialCommitmentUpdate,
    InstallmentPayRequest,
)
from app.schemas.transaction import TransactionCreate
from app.services import financing_service
from app.services.card_service import create_card
from app.services.dashboard_service import get_summary
from app.services.invoice_service import list_invoices, pay_invoice
from app.services.purchase_service import create_purchase
from app.utils import dates
from app.utils.dates import invoice_competence_for_purchase
from app.utils.money import split_installments
from tests.conftest import make_account


# --- Parcelamento -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "total,count",
    [("10.00", 60), ("1.00", 60), ("100.00", 60), ("1000.00", 3), ("1433.00", 36), ("0.05", 3), ("99.99", 7)],
)
def test_split_never_creates_negative_or_uneven_installments(total, count):
    """Antes: 10,00 em 60x gerava a última parcela de -0,03."""
    parts = split_installments(Decimal(total), count)
    assert sum(parts) == Decimal(total)
    assert min(parts) >= Decimal("0.01")
    assert max(parts) - min(parts) <= Decimal("0.01")
    assert all(p == p.quantize(Decimal("0.01")) for p in parts)


# --- Datas ------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "purchase,closing_day,expected",
    [
        (date(2026, 2, 28), 31, date(2026, 3, 1)),  # fev fecha no dia 28 → compra no dia 28 vai pra março
        (date(2026, 4, 30), 31, date(2026, 5, 1)),
        (date(2027, 2, 28), 30, date(2027, 3, 1)),
        (date(2026, 2, 27), 31, date(2026, 2, 1)),  # véspera do fechamento continua em fevereiro
        (date(2026, 3, 30), 31, date(2026, 3, 1)),
    ],
)
def test_closing_day_beyond_month_length_uses_real_closing_date(purchase, closing_day, expected):
    assert invoice_competence_for_purchase(purchase, closing_day) == expected


def test_local_today_uses_app_timezone_not_server_utc(monkeypatch):
    """Na Vercel o servidor está em UTC: 02:30 UTC de 01/10 ainda é 30/09 no Brasil."""

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 1, 2, 30, tzinfo=timezone.utc).astimezone(tz)

    monkeypatch.setattr(dates, "datetime", FrozenDatetime)
    assert dates.local_today() == date(2026, 9, 30)


# --- Validação de valores ----------------------------------------------------------------------

@pytest.mark.parametrize("amount", ["-1000", "0", "0.001", "1e15"])
def test_money_inputs_reject_negative_zero_sub_cent_and_overflow(amount):
    """Antes: pagar parcela ou amortizar com valor negativo CREDITAVA a conta."""
    with pytest.raises(PydanticValidationError):
        InstallmentPayRequest(payment_date=date(2026, 1, 1), account_id="00000000-0000-0000-0000-000000000001", paid_amount=amount)
    with pytest.raises(PydanticValidationError):
        AmortizationCreate(date=date(2026, 1, 1), paid_amount=amount, type=AmortizationType.REDUCAO_PRAZO,
                           account_id="00000000-0000-0000-0000-000000000001")
    with pytest.raises(PydanticValidationError):
        TransactionCreate(description="x", type="DESPESA", amount=amount, competence_date=date(2026, 1, 1))


# --- Financiamentos ----------------------------------------------------------------------------

def _car_financing(db, account, institution, total=36, amount="1433.00"):
    return financing_service.create_commitment(
        db,
        account.user_id,
        FinancialCommitmentCreate(
            institution_id=institution.id,
            type=CommitmentType.FINANCIAMENTO,
            name="Carro",
            financed_amount=Decimal("40000.00"),
            installments_total=total,
            default_installment_amount=Decimal(amount),
            start_date=date(2026, 1, 10),
            due_day=10,
        ),
    )


def _installments(db, commitment):
    return financing_repository.list_installments(db, commitment["id"])


def test_outstanding_balance_is_consistent_from_creation(db, account, institution):
    """Antes: 40 mil na criação e 36 x 1.433 - 1.433 = 50.155 depois do 1º pagamento."""
    commitment = _car_financing(db, account, institution)
    assert commitment["outstanding_balance"] == Decimal("51588.00")  # 36 x 1.433

    first = _installments(db, commitment)[0]
    financing_service.pay_installment(
        db, account.user_id, commitment["id"], first.id,
        InstallmentPayRequest(payment_date=date(2026, 1, 10), account_id=account.id),
    )
    after = financing_service.get_commitment_with_indicators(db, account.user_id, commitment["id"])
    assert after["outstanding_balance"] == Decimal("50155.00")


def test_installment_value_reduction_amortization_is_disabled(db, account, institution):
    commitment = _car_financing(db, account, institution)
    with pytest.raises(ValidationError, match="redução do valor das parcelas"):
        financing_service.create_amortization(
            db, account.user_id, commitment["id"],
            AmortizationCreate(date=date(2026, 2, 1), paid_amount=Decimal("2000.00"),
                               type=AmortizationType.REDUCAO_PARCELA, account_id=account.id),
        )


def test_amortizing_last_installments_with_discount_keeps_others_unchanged(db, account, institution):
    """Caso real do usuário: quitar as 2 últimas (2 x 1.433 = 2.866) pagando 2.500."""
    commitment = _car_financing(db, account, institution)
    financing_service.create_amortization(
        db, account.user_id, commitment["id"],
        AmortizationCreate(date=date(2026, 2, 1), paid_amount=Decimal("2500.00"),
                           type=AmortizationType.REDUCAO_PRAZO, account_id=account.id,
                           installment_numbers=[35, 36]),
    )
    result = financing_service.get_commitment_with_indicators(db, account.user_id, commitment["id"])
    pending = [i for i in _installments(db, commitment) if i.status.value == "PENDENTE"]
    assert len(pending) == 34
    assert all(i.updated_amount == Decimal("1433.00") for i in pending)
    assert result["outstanding_balance"] == Decimal("48722.00")  # 34 x 1.433
    assert result["accumulated_savings"] == Decimal("366.00")


def test_amortization_cannot_cost_more_than_selected_installments(db, account, institution):
    commitment = _car_financing(db, account, institution)
    with pytest.raises(ValidationError, match="maior que a soma"):
        financing_service.create_amortization(
            db, account.user_id, commitment["id"],
            AmortizationCreate(date=date(2026, 2, 1), paid_amount=Decimal("3000.00"),
                               type=AmortizationType.REDUCAO_PRAZO, account_id=account.id,
                               installment_numbers=[35, 36]),
        )


def test_early_installment_payment_discount_counts_as_savings(db, account, institution):
    """Pagar a próxima parcela antes do vencimento com desconto (1.433 → 1.400)."""
    commitment = _car_financing(db, account, institution)
    first = _installments(db, commitment)[0]
    financing_service.pay_installment(
        db, account.user_id, commitment["id"], first.id,
        InstallmentPayRequest(payment_date=date(2026, 1, 5), account_id=account.id, paid_amount=Decimal("1400.00")),
    )
    result = financing_service.get_commitment_with_indicators(db, account.user_id, commitment["id"])
    assert result["accumulated_savings"] == Decimal("33.00")
    assert result["total_paid"] == Decimal("1400.00")


def test_cancelled_financing_rejects_payments_and_leaves_net_worth(db, account, institution):
    commitment = _car_financing(db, account, institution)
    before = get_summary(db, account.user_id)
    assert before["gross_worth"] - before["net_worth"] == Decimal("51588.00")

    financing_service.update_commitment(
        db, account.user_id, commitment["id"], FinancialCommitmentUpdate(status=CommitmentStatus.CANCELADO)
    )
    after = get_summary(db, account.user_id)
    assert after["net_worth"] == after["gross_worth"]

    first = _installments(db, commitment)[0]
    with pytest.raises(ValidationError, match="ativos"):
        financing_service.pay_installment(
            db, account.user_id, commitment["id"], first.id,
            InstallmentPayRequest(payment_date=date(2026, 1, 10), account_id=account.id),
        )


# --- Patrimônio x saldo ------------------------------------------------------------------------

def test_net_worth_matches_balance_after_paying_a_future_invoice(db, user, account, institution, expense_category):
    """Antes: pagar hoje a fatura do mês seguinte tirava o valor do saldo, mas não do patrimônio."""
    card = create_card(
        db, user.id,
        CreditCardCreate(institution_id=institution.id, name="Cartão", credit_limit=Decimal("5000.00"),
                         closing_day=1, due_day=10, default_payment_account_id=account.id),
    )
    today = dates.local_today()
    create_purchase(
        db, user.id, card["id"],
        CreditCardPurchaseCreate(description="Mercado", total_amount=Decimal("300.00"), installments_total=1,
                                 purchase_date=today, category_id=expense_category.id),
    )
    invoice = list_invoices(db, user.id, card["id"])[0]
    assert invoice.competence > today  # compra após o fechamento → fatura com competência futura
    pay_invoice(db, user.id, invoice.id, today, account.id)

    summary = get_summary(db, user.id)
    assert summary["available_balance"] == Decimal("700.00")
    assert summary["gross_worth"] == summary["available_balance"]


def test_inactive_accounts_are_excluded_from_both_balance_and_worth(db, user, account, institution):
    hidden = make_account(db, user, institution, name="Antiga", initial_balance=Decimal("500.00"))
    hidden.active = False
    db.commit()
    summary = get_summary(db, user.id)
    assert summary["available_balance"] == Decimal("1000.00")
    assert summary["gross_worth"] == Decimal("1000.00")
