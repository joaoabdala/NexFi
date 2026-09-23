"""Regressões do lote final da auditoria: exclusão de usuário, faturas, login e validações."""

from decimal import Decimal

import pytest
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import func, select

from app.core.exceptions import TooManyRequestsError, UnauthorizedError, ValidationError
from app.core.security import hash_password, hash_refresh_token
from app.models import Account, CreditCardInvoice, Transaction, User
from app.models.enums import (
    AmortizationType,
    CategoryKind,
    CommitmentType,
    InvoiceStatus,
    RecurrenceFrequency,
    TransactionType,
    UserRole,
)
from app.repositories import auth_repository, financing_repository
from app.schemas.account import BalanceAdjustmentCreate
from app.schemas.auth import UpdateProfileRequest
from app.schemas.budget import BudgetCreate
from app.schemas.card import CreditCardCreate, CreditCardPurchaseCreate
from app.schemas.category import CategoryCreate
from app.schemas.financing import AmortizationCreate, FinancialCommitmentCreate, InstallmentPayRequest
from app.schemas.goal import GoalCreate
from app.schemas.recurrence import RecurrenceCreate
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.schemas.transfer import TransferCreate
from app.services import (
    account_service,
    admin_user_service,
    auth_service,
    budget_service,
    category_service,
    financing_service,
    goal_service,
    login_throttle_service,
    recurrence_service,
    transaction_service,
    transfer_service,
)
from app.services.card_service import create_card
from app.services.invoice_service import list_invoices, pay_invoice
from app.services.purchase_service import create_purchase
from app.utils.dates import local_today


def _card(db, user, account, institution, closing_day=1):
    return create_card(
        db, user.id,
        CreditCardCreate(institution_id=institution.id, name="Cartão", credit_limit=Decimal("5000.00"),
                         closing_day=closing_day, due_day=10, default_payment_account_id=account.id),
    )


def _purchase(db, user, card, amount, category):
    return create_purchase(
        db, user.id, card["id"],
        CreditCardPurchaseCreate(description="Compra", total_amount=Decimal(amount), installments_total=1,
                                 purchase_date=local_today(), category_id=category.id),
    )


# --- Exclusão de usuário ------------------------------------------------------------------------

def test_admin_can_delete_user_with_every_kind_of_data(db, user, account, account2, institution, expense_category):
    """Antes: qualquer dado (até uma transação) fazia a exclusão falhar com IntegrityError."""
    admin = User(email="admin@nexfi.app", password_hash=hash_password("senha12345"), name="Admin", role=UserRole.ADMIN)
    db.add(admin)
    db.commit()
    today = local_today()

    card = _card(db, user, account, institution)
    _purchase(db, user, card, "150.00", expense_category)
    pay_invoice(db, user.id, list_invoices(db, user.id, card["id"])[0].id, today, account.id)

    commitment = financing_service.create_commitment(
        db, user.id,
        FinancialCommitmentCreate(institution_id=institution.id, type=CommitmentType.FINANCIAMENTO, name="Carro",
                                  financed_amount=Decimal("1000.00"), installments_total=10,
                                  default_installment_amount=Decimal("100.00"), start_date=today, due_day=10),
    )
    installments = financing_repository.list_installments(db, commitment["id"])
    financing_service.pay_installment(db, user.id, commitment["id"], installments[0].id,
                                      InstallmentPayRequest(payment_date=today, account_id=account.id))
    financing_service.create_amortization(
        db, user.id, commitment["id"],
        AmortizationCreate(date=today, paid_amount=Decimal("150.00"), type=AmortizationType.REDUCAO_PRAZO,
                           account_id=account.id, installment_numbers=[9, 10]),
    )
    transfer_service.create_transfer(db, user.id, TransferCreate(from_account_id=account.id, to_account_id=account2.id,
                                                                 amount=Decimal("50.00"), date=today))
    account_service.create_balance_adjustment(db, user.id, account.id,
                                              BalanceAdjustmentCreate(informed_balance=Decimal("700.00"), date=today))
    recurrence_service.create_recurrence(
        db, user.id,
        RecurrenceCreate(description="Academia", type=TransactionType.DESPESA, amount=Decimal("90.00"),
                         account_id=account.id, category_id=expense_category.id,
                         frequency=RecurrenceFrequency.MENSAL, start_date=today),
    )
    budget_service.create_budget(db, user.id, BudgetCreate(category_id=expense_category.id, amount=Decimal("500.00")))
    goal_service.create_goal(db, user.id, GoalCreate(name="Reserva", target_amount=Decimal("10000.00"),
                                                     linked_account_id=account.id))
    category_service.create_category(db, user.id, CategoryCreate(name="Sub", kind=CategoryKind.DESPESA,
                                                                 parent_id=expense_category.id))
    auth_service.login(db, user.email, "senha12345")

    user_id = user.id
    admin_user_service.delete_user(db, admin, user_id)

    assert db.get(User, user_id) is None
    assert db.scalar(select(func.count()).select_from(Transaction).where(Transaction.user_id == user_id)) == 0
    assert db.scalar(select(func.count()).select_from(Account).where(Account.user_id == user_id)) == 0
    assert db.scalar(select(func.count()).select_from(CreditCardInvoice)) == 0
    assert db.get(User, admin.id) is not None  # os dados de outros usuários ficam intactos


# --- Faturas ------------------------------------------------------------------------------------

def test_purchase_on_paid_invoice_reopens_it_and_next_payment_covers_only_difference(db, user, account, institution, expense_category):
    """Antes: pagar uma fatura antes do fechamento bloqueava qualquer compra nova no período."""
    card = _card(db, user, account, institution)
    _purchase(db, user, card, "200.00", expense_category)
    invoice = list_invoices(db, user.id, card["id"])[0]
    pay_invoice(db, user.id, invoice.id, local_today(), account.id)
    assert invoice.status == InvoiceStatus.PAGA

    _purchase(db, user, card, "80.00", expense_category)  # não pode mais dar erro
    db.refresh(invoice)
    assert invoice.status != InvoiceStatus.PAGA

    pay_invoice(db, user.id, invoice.id, local_today(), account.id)
    payments = list(db.scalars(select(Transaction.amount).where(
        Transaction.invoice_id == invoice.id, Transaction.type == TransactionType.PAGAMENTO_FATURA)))
    assert sorted(payments) == [Decimal("80.00"), Decimal("200.00")]
    assert invoice.status == InvoiceStatus.PAGA
    with pytest.raises(ValidationError, match="já foi paga"):
        pay_invoice(db, user.id, invoice.id, local_today(), account.id)


# --- Login e sessões ----------------------------------------------------------------------------

def test_login_is_locked_after_repeated_failures_per_email(db, user):
    for _ in range(login_throttle_service.MAX_FAILURES_PER_EMAIL):
        with pytest.raises(UnauthorizedError):
            auth_service.login(db, user.email, "errada", client_ip="10.0.0.1")
    # bloqueada até para a senha certa, e de outro IP
    with pytest.raises(TooManyRequestsError, match="Tente novamente"):
        auth_service.login(db, user.email, "senha12345", client_ip="10.0.0.2")


def test_login_is_locked_per_ip_across_many_emails(db, user):
    for i in range(login_throttle_service.MAX_FAILURES_PER_IP):
        with pytest.raises(UnauthorizedError):
            auth_service.login(db, f"alvo{i}@exemplo.com", "x", client_ip="203.0.113.9")
    with pytest.raises(TooManyRequestsError):
        auth_service.login(db, user.email, "senha12345", client_ip="203.0.113.9")
    assert auth_service.login(db, user.email, "senha12345", client_ip="198.51.100.1").access_token


def test_successful_login_resets_email_failures(db, user):
    for _ in range(login_throttle_service.MAX_FAILURES_PER_EMAIL - 1):
        with pytest.raises(UnauthorizedError):
            auth_service.login(db, user.email, "errada")
    auth_service.login(db, user.email, "senha12345")
    for _ in range(login_throttle_service.MAX_FAILURES_PER_EMAIL - 1):
        with pytest.raises(UnauthorizedError):
            auth_service.login(db, user.email, "errada")
    assert auth_service.login(db, user.email, "senha12345").access_token


def test_refresh_token_can_only_be_rotated_once(db, user):
    """Dois refresh simultâneos com o mesmo token: só um pode vencer."""
    tokens = auth_service.login(db, user.email, "senha12345")
    record = auth_repository.get_refresh_token_by_hash(db, hash_refresh_token(tokens.refresh_token))
    assert auth_repository.revoke_if_active(db, record) is True
    assert auth_repository.revoke_if_active(db, record) is False


# --- Validações ---------------------------------------------------------------------------------

@pytest.mark.parametrize("field", ["account_id", "amount", "description", "competence_date"])
def test_transaction_update_rejects_clearing_required_fields(db, user, account, expense_category, field):
    txn = transaction_service.create_transaction(
        db, user.id,
        TransactionCreate(
            description="Mercado", type=TransactionType.DESPESA, amount=Decimal("50.00"), account_id=account.id,
            category_id=expense_category.id, competence_date=local_today(), payment_date=local_today(),
            status="CONFIRMADA"),
    )
    with pytest.raises(ValidationError, match="não pode ficar vazio"):
        transaction_service.update_transaction(db, user.id, txn.id, TransactionUpdate(**{field: None}))


def test_amortization_rejects_repeated_installment_numbers(db, user, account, institution):
    commitment = financing_service.create_commitment(
        db, user.id,
        FinancialCommitmentCreate(institution_id=institution.id, type=CommitmentType.FINANCIAMENTO, name="Carro",
                                  financed_amount=Decimal("1000.00"), installments_total=10,
                                  default_installment_amount=Decimal("100.00"), start_date=local_today(), due_day=10),
    )
    with pytest.raises(ValidationError, match="mais de uma vez"):
        financing_service.create_amortization(
            db, user.id, commitment["id"],
            AmortizationCreate(date=local_today(), paid_amount=Decimal("150.00"), type=AmortizationType.REDUCAO_PRAZO,
                               account_id=account.id, installment_numbers=[10, 10]),
        )


@pytest.mark.parametrize("payload", [{"timezone": "Marte/Olympus"}, {"timezone": "x" * 70}, {"locale": "portugues"}])
def test_profile_rejects_invalid_timezone_or_locale(payload):
    with pytest.raises(PydanticValidationError):
        UpdateProfileRequest(**payload)


def test_profile_accepts_valid_values():
    assert UpdateProfileRequest(timezone="America/Sao_Paulo", locale="pt-BR").timezone == "America/Sao_Paulo"
