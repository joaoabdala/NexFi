from datetime import date
from decimal import Decimal

import pytest

from app.core.exceptions import ValidationError
from app.models.enums import CommitmentInstallmentStatus, CommitmentType, TransactionType
from app.models.transaction import Transaction
from app.repositories import financing_repository
from app.schemas.financing import FinancialCommitmentCreate, InstallmentPayRequest
from app.services.balance_service import get_account_balance
from app.services.financing_service import (
    commitment_with_indicators,
    create_commitment,
    get_commitment,
    pay_installment,
)


def _make_commitment(db, account, institution):
    return create_commitment(
        db,
        account.user_id,
        FinancialCommitmentCreate(
            institution_id=institution.id,
            type=CommitmentType.FINANCIAMENTO,
            name="Financiamento Teste",
            financed_amount=Decimal("4800.00"),
            installments_total=48,
            default_installment_amount=Decimal("100.00"),
            start_date=date(2026, 1, 10),
            due_day=10,
        ),
    )


def test_commitment_creation_generates_full_schedule(db, account, institution):
    commitment = _make_commitment(db, account, institution)
    installments = financing_repository.list_installments(db, commitment["id"])
    assert len(installments) == 48
    assert all(i.status == CommitmentInstallmentStatus.PENDENTE for i in installments)
    assert commitment["outstanding_balance"] == Decimal("4800.00")


def test_paying_installment_debits_account_and_reduces_outstanding_balance(db, account, institution):
    commitment = _make_commitment(db, account, institution)
    installments = financing_repository.list_installments(db, commitment["id"])
    first = installments[0]
    balance_before = get_account_balance(db, account)

    paid = pay_installment(
        db,
        account.user_id,
        commitment["id"],
        first.id,
        InstallmentPayRequest(payment_date=date(2026, 2, 10), account_id=account.id),
    )

    assert paid.status == CommitmentInstallmentStatus.PAGA
    assert get_account_balance(db, account) == balance_before - Decimal("100.00")

    updated = get_commitment(db, account.user_id, commitment["id"])
    assert updated.outstanding_balance == Decimal("4700.00")

    txn = db.get(Transaction, paid.transaction_id)
    assert txn.type == TransactionType.PAGAMENTO_FINANCIAMENTO


def test_cannot_pay_installment_twice(db, account, institution):
    commitment = _make_commitment(db, account, institution)
    first = financing_repository.list_installments(db, commitment["id"])[0]
    payload = InstallmentPayRequest(payment_date=date(2026, 2, 10), account_id=account.id)
    pay_installment(db, account.user_id, commitment["id"], first.id, payload)
    with pytest.raises(ValidationError):
        pay_installment(db, account.user_id, commitment["id"], first.id, payload)
