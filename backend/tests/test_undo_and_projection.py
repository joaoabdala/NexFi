"""Desfazer pagamentos/transferências e faturas de cartão na projeção de saldo."""

from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.core.exceptions import ValidationError
from app.models import Transaction
from app.models.enums import (
    CommitmentInstallmentStatus,
    CommitmentStatus,
    CommitmentType,
    InvoiceStatus,
    TransactionStatus,
    TransactionType,
)
from app.repositories import financing_repository
from app.schemas.card import CreditCardCreate, CreditCardPurchaseCreate
from app.schemas.financing import FinancialCommitmentCreate, InstallmentPayRequest
from app.schemas.transfer import TransferCreate
from app.services import financing_service, transaction_service, transfer_service
from app.services.balance_service import get_account_balance
from app.services.card_service import create_card
from app.services.dashboard_service import get_projection
from app.services.invoice_service import (
    compute_invoice_paid,
    list_invoices,
    pay_invoice,
    undo_invoice_payment,
)
from app.services.purchase_service import create_purchase
from app.utils.dates import local_today


def _card_with_purchase(db, user, account, institution, category, amount="300.00", closing_day=1, due_day=10):
    card = create_card(
        db, user.id,
        CreditCardCreate(institution_id=institution.id, name="Cartão", credit_limit=Decimal("5000.00"),
                         closing_day=closing_day, due_day=due_day, default_payment_account_id=account.id),
    )
    create_purchase(
        db, user.id, card["id"],
        CreditCardPurchaseCreate(description="Mercado", total_amount=Decimal(amount), installments_total=1,
                                 purchase_date=local_today(), category_id=category.id),
    )
    return card, list_invoices(db, user.id, card["id"])[0]


# --- Desfazer pagamento de fatura ---------------------------------------------------------------

def test_undo_invoice_payment_returns_money_and_reopens_invoice(db, user, account, institution, expense_category):
    card, invoice = _card_with_purchase(db, user, account, institution, expense_category)
    pay_invoice(db, user.id, invoice.id, local_today(), account.id)
    assert get_account_balance(db, account) == Decimal("700.00")

    undo_invoice_payment(db, user.id, invoice.id)

    assert get_account_balance(db, account) == Decimal("1000.00")
    assert invoice.status != InvoiceStatus.PAGA
    assert invoice.payment_date is None
    cancelled = db.scalars(select(Transaction).where(Transaction.invoice_id == invoice.id,
                                                     Transaction.type == TransactionType.PAGAMENTO_FATURA)).one()
    assert cancelled.status == TransactionStatus.CANCELADA  # histórico preservado
    pay_invoice(db, user.id, invoice.id, local_today(), account.id)  # pode pagar de novo
    assert invoice.status == InvoiceStatus.PAGA


def test_undo_one_of_two_payments_keeps_the_other(db, user, account, institution, expense_category):
    card, invoice = _card_with_purchase(db, user, account, institution, expense_category, amount="200.00")
    pay_invoice(db, user.id, invoice.id, local_today(), account.id)
    create_purchase(db, user.id, card["id"],
                    CreditCardPurchaseCreate(description="Extra", total_amount=Decimal("50.00"), installments_total=1,
                                             purchase_date=local_today(), category_id=expense_category.id))
    pay_invoice(db, user.id, invoice.id, local_today(), account.id)

    undo_invoice_payment(db, user.id, invoice.id)  # desfaz o mais recente (50)

    assert compute_invoice_paid(db, invoice) == Decimal("200.00")
    assert invoice.status != InvoiceStatus.PAGA
    assert get_account_balance(db, account) == Decimal("800.00")


def test_undo_without_active_payment_is_rejected(db, user, account, institution, expense_category):
    _, invoice = _card_with_purchase(db, user, account, institution, expense_category)
    with pytest.raises(ValidationError, match="Não há pagamento"):
        undo_invoice_payment(db, user.id, invoice.id)


# --- Desfazer pagamento de parcela ---------------------------------------------------------------

def _financing(db, user, institution, total=2):
    return financing_service.create_commitment(
        db, user.id,
        FinancialCommitmentCreate(institution_id=institution.id, type=CommitmentType.FINANCIAMENTO, name="Carro",
                                  financed_amount=Decimal("2000.00"), installments_total=total,
                                  default_installment_amount=Decimal("1000.00"), start_date=local_today(), due_day=10),
    )


def test_undo_installment_payment_returns_money_and_reopens_paid_off_financing(db, user, account, institution):
    commitment = _financing(db, user, institution, total=1)
    installment = financing_repository.list_installments(db, commitment["id"])[0]
    financing_service.pay_installment(db, user.id, commitment["id"], installment.id,
                                      InstallmentPayRequest(payment_date=local_today(), account_id=account.id,
                                                            paid_amount=Decimal("950.00")))
    assert financing_service.get_commitment(db, user.id, commitment["id"]).status == CommitmentStatus.QUITADO
    assert get_account_balance(db, account) == Decimal("50.00")

    financing_service.undo_installment_payment(db, user.id, commitment["id"], installment.id)

    db.refresh(installment)
    result = financing_service.get_commitment_with_indicators(db, user.id, commitment["id"])
    assert installment.status == CommitmentInstallmentStatus.PENDENTE
    assert installment.paid_amount is None
    assert result["status"] == CommitmentStatus.ATIVO
    assert result["outstanding_balance"] == Decimal("1000.00")
    assert result["accumulated_savings"] == Decimal("0.00")  # desconto da antecipação some junto
    assert get_account_balance(db, account) == Decimal("1000.00")


def test_undo_pending_installment_is_rejected(db, user, account, institution):
    commitment = _financing(db, user, institution)
    installment = financing_repository.list_installments(db, commitment["id"])[0]
    with pytest.raises(ValidationError, match="parcela paga"):
        financing_service.undo_installment_payment(db, user.id, commitment["id"], installment.id)


# --- Desfazer transferência ----------------------------------------------------------------------

def test_cancel_transfer_restores_both_balances_once(db, user, account, account2):
    transfer = transfer_service.create_transfer(
        db, user.id, TransferCreate(from_account_id=account.id, to_account_id=account2.id,
                                    amount=Decimal("250.00"), date=local_today()))
    assert get_account_balance(db, account2) == Decimal("750.00")  # account2 começa com 500
    transfer_service.cancel_transfer(db, user.id, transfer.id)
    assert get_account_balance(db, account) == Decimal("1000.00")
    assert get_account_balance(db, account2) == Decimal("500.00")
    with pytest.raises(ValidationError, match="já foi desfeita"):
        transfer_service.cancel_transfer(db, user.id, transfer.id)


# --- "Desfazer" a partir da lista de transações --------------------------------------------------

def test_reverse_dispatches_to_the_owning_module(db, user, account, account2, institution, expense_category):
    transfer = transfer_service.create_transfer(
        db, user.id, TransferCreate(from_account_id=account.id, to_account_id=account2.id,
                                    amount=Decimal("100.00"), date=local_today()))
    leg = db.scalars(select(Transaction).where(Transaction.transfer_id == transfer.id)).first()
    transaction_service.reverse_transaction(db, user.id, leg.id)
    assert get_account_balance(db, account2) == Decimal("500.00")  # saldo inicial de account2

    _, invoice = _card_with_purchase(db, user, account, institution, expense_category)
    pay_invoice(db, user.id, invoice.id, local_today(), account.id)
    payment = db.scalars(select(Transaction).where(Transaction.invoice_id == invoice.id,
                                                   Transaction.type == TransactionType.PAGAMENTO_FATURA)).one()
    transaction_service.reverse_transaction(db, user.id, payment.id)
    assert invoice.status != InvoiceStatus.PAGA

    commitment = _financing(db, user, institution)
    installment = financing_repository.list_installments(db, commitment["id"])[0]
    paid = financing_service.pay_installment(db, user.id, commitment["id"], installment.id,
                                             InstallmentPayRequest(payment_date=local_today(), account_id=account.id))
    transaction_service.reverse_transaction(db, user.id, paid.transaction_id or installment.transaction_id)
    db.refresh(installment)
    assert installment.status == CommitmentInstallmentStatus.PENDENTE
    assert get_account_balance(db, account) == Decimal("1000.00")


def test_reverse_rejects_regular_transactions(db, user, account, expense_category):
    from app.schemas.transaction import TransactionCreate

    txn = transaction_service.create_transaction(
        db, user.id, TransactionCreate(description="Padaria", type=TransactionType.DESPESA, amount=Decimal("10.00"),
                                       account_id=account.id, category_id=expense_category.id,
                                       competence_date=local_today(), payment_date=local_today(), status="CONFIRMADA"))
    with pytest.raises(ValidationError, match="Cancelar"):
        transaction_service.reverse_transaction(db, user.id, txn.id)


# --- Projeção de saldo com faturas ---------------------------------------------------------------

def test_projection_subtracts_open_card_invoices_due_within_horizon(db, user, account, institution, expense_category):
    """Antes: a projeção ignorava o cartão — compras no cartão não têm conta até a fatura ser paga."""
    card, invoice = _card_with_purchase(db, user, account, institution, expense_category, amount="300.00")
    horizon = (invoice.due_date - local_today()).days + 1

    projection = get_projection(db, user.id, horizon)
    assert projection["card_invoices_due"] == Decimal("300.00")
    assert projection["projected_balance"] == Decimal("700.00")

    short = get_projection(db, user.id, max(1, (invoice.due_date - local_today()).days - 1))
    if invoice.due_date - local_today() > timedelta(days=1):
        assert short["card_invoices_due"] == Decimal("0.00")  # vence depois do horizonte

    pay_invoice(db, user.id, invoice.id, local_today(), account.id)
    after = get_projection(db, user.id, horizon)
    assert after["card_invoices_due"] == Decimal("0.00")
    assert after["projected_balance"] == Decimal("700.00")  # agora já saiu do saldo atual
