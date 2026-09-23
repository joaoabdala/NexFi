import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.account import Account
from app.models.balance_adjustment import BalanceAdjustment
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.repositories import account_repository, institution_repository
from app.schemas.account import AccountCreate, AccountUpdate, BalanceAdjustmentCreate
from app.services.balance_service import get_account_balance
from app.utils.money import quantize


def list_accounts(db: Session, user_id: uuid.UUID, active_only: bool = False) -> list[dict]:
    accounts = account_repository.list_by_user(db, user_id, active_only)
    return [_with_balance(db, account) for account in accounts]


def get_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> Account:
    account = account_repository.get_by_id(db, user_id, account_id)
    if not account:
        raise NotFoundError("Conta não encontrada.")
    return account


def get_account_with_balance(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> dict:
    account = get_account(db, user_id, account_id)
    return _with_balance(db, account)


def _with_balance(db: Session, account: Account) -> dict:
    balance = get_account_balance(db, account)
    return {
        "id": account.id,
        "institution_id": account.institution_id,
        "name": account.name,
        "type": account.type,
        "initial_balance": account.initial_balance,
        "initial_balance_date": account.initial_balance_date,
        "active": account.active,
        "include_in_available_worth": account.include_in_available_worth,
        "include_in_invested_worth": account.include_in_invested_worth,
        "note": account.note,
        "current_balance": balance,
        "institution_name": account.institution.name if account.institution else None,
    }


def create_account(db: Session, user_id: uuid.UUID, payload: AccountCreate) -> dict:
    institution = institution_repository.get_by_id(db, user_id, payload.institution_id)
    if not institution:
        raise ValidationError("Instituição inválida.")
    account = Account(user_id=user_id, **payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return _with_balance(db, account)


def update_account(
    db: Session, user_id: uuid.UUID, account_id: uuid.UUID, payload: AccountUpdate
) -> dict:
    account = get_account(db, user_id, account_id)
    data = payload.model_dump(exclude_unset=True)
    if "institution_id" in data and data["institution_id"] is not None:
        institution = institution_repository.get_by_id(db, user_id, data["institution_id"])
        if not institution:
            raise ValidationError("Instituição inválida.")
    for field, value in data.items():
        setattr(account, field, value)
    db.add(account)
    db.commit()
    db.refresh(account)
    return _with_balance(db, account)


def deactivate_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> None:
    account = get_account(db, user_id, account_id)
    account.active = False
    db.add(account)
    db.commit()


def create_balance_adjustment(
    db: Session, user_id: uuid.UUID, account_id: uuid.UUID, payload: BalanceAdjustmentCreate
) -> BalanceAdjustment:
    account = get_account(db, user_id, account_id)
    previous_balance = get_account_balance(db, account)
    informed = quantize(payload.informed_balance)
    difference = quantize(informed - previous_balance)
    if difference == Decimal("0"):
        raise ValidationError("O saldo informado já corresponde ao saldo atual da conta.")

    try:
        transaction = Transaction(
            user_id=user_id,
            account_id=account.id,
            category_id=None,
            description="Ajuste de saldo",
            type=TransactionType.AJUSTE,
            amount=difference,
            competence_date=payload.date,
            payment_date=payload.date,
            status=TransactionStatus.CONFIRMADA,
            origin="AJUSTE_SALDO",
        )
        db.add(transaction)
        db.flush()

        adjustment = BalanceAdjustment(
            user_id=user_id,
            account_id=account.id,
            previous_balance=previous_balance,
            informed_balance=informed,
            difference=difference,
            date=payload.date,
            note=payload.note,
            transaction_id=transaction.id,
        )
        db.add(adjustment)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(adjustment)
    return adjustment
