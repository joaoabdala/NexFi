import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.security import hash_password
from app.models import (
    Account,
    Amortization,
    AmortizationInstallment,
    BalanceAdjustment,
    Budget,
    Category,
    CommitmentInstallment,
    CreditCard,
    CreditCardInstallment,
    CreditCardInvoice,
    CreditCardPurchase,
    FinancialCommitment,
    FinancialGoal,
    FinancialInstitution,
    RecurrenceRule,
    RefreshToken,
    Transaction,
    Transfer,
)
from app.models.enums import UserRole
from app.models.user import User
from app.repositories import auth_repository, user_repository
from app.schemas.admin import AdminUserCreate, AdminUserUpdate


def list_users(db: Session) -> list[User]:
    return user_repository.list_all(db)


def get_user(db: Session, user_id: uuid.UUID) -> User:
    user = user_repository.get_by_id(db, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado.")
    return user


def create_user(db: Session, payload: AdminUserCreate) -> User:
    if user_repository.get_by_email(db, payload.email):
        raise ConflictError("Já existe um usuário com este e-mail.")

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        name=payload.name,
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _ensure_at_least_one_active_admin_remains(db: Session, target: User, payload: AdminUserUpdate) -> None:
    """Impede que a última conta de administrador ativa seja rebaixada ou desativada."""
    is_admin = target.role == UserRole.ADMIN and target.is_active
    would_stay_admin = (
        (payload.role if payload.role is not None else target.role) == UserRole.ADMIN
        and (payload.is_active if payload.is_active is not None else target.is_active)
    )
    if is_admin and not would_stay_admin:
        remaining = user_repository.count_active_admins(db, exclude_user_id=target.id)
        if remaining < 1:
            raise ValidationError(
                "Não é possível remover o último administrador ativo do sistema."
            )


def update_user(db: Session, user_id: uuid.UUID, payload: AdminUserUpdate) -> User:
    user = get_user(db, user_id)
    data = payload.model_dump(exclude_unset=True, exclude={"password"})

    if "email" in data and data["email"] is not None:
        data["email"] = data["email"].lower()
        existing = user_repository.get_by_email(db, data["email"])
        if existing and existing.id != user.id:
            raise ConflictError("Já existe um usuário com este e-mail.")

    _ensure_at_least_one_active_admin_remains(db, user, payload)

    for field, value in data.items():
        setattr(user, field, value)
    if payload.password:
        user.password_hash = hash_password(payload.password)
        auth_repository.delete_all_refresh_tokens(db, user.id)
    if payload.is_active is False:
        auth_repository.delete_all_refresh_tokens(db, user.id)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, requesting_user: User, user_id: uuid.UUID) -> None:
    if requesting_user.id == user_id:
        raise ValidationError("Você não pode excluir a própria conta.")

    user = get_user(db, user_id)
    if user.role == UserRole.ADMIN and user.is_active:
        remaining = user_repository.count_active_admins(db, exclude_user_id=user.id)
        if remaining < 1:
            raise ValidationError("Não é possível excluir o último administrador ativo do sistema.")

    try:
        _delete_user_data(db, user.id)
        db.delete(user)
        db.commit()
    except Exception:
        db.rollback()
        raise


def _delete_user_data(db: Session, user_id: uuid.UUID) -> None:
    """Apaga os dados financeiros do usuário em ordem de dependência.

    As FKs entre tabelas do próprio usuário são RESTRICT (ex.: conta ← transferência, cartão ←
    fatura), de propósito: o app nunca apaga histórico por acidente. Por isso o ON DELETE
    CASCADE a partir de users não basta — o banco recusava excluir quem tivesse qualquer dado.
    """
    card_ids = select(CreditCard.id).where(CreditCard.user_id == user_id)
    commitment_ids = select(FinancialCommitment.id).where(FinancialCommitment.user_id == user_id)
    amortization_ids = select(Amortization.id).where(Amortization.user_id == user_id)
    purchase_ids = select(CreditCardPurchase.id).where(CreditCardPurchase.user_id == user_id)
    steps = [
        delete(BalanceAdjustment).where(BalanceAdjustment.user_id == user_id),
        delete(Transaction).where(Transaction.user_id == user_id),
        delete(Transfer).where(Transfer.user_id == user_id),
        delete(AmortizationInstallment).where(AmortizationInstallment.amortization_id.in_(amortization_ids)),
        update(CommitmentInstallment)
        .where(CommitmentInstallment.commitment_id.in_(commitment_ids))
        .values(amortization_id=None),
        delete(Amortization).where(Amortization.user_id == user_id),
        delete(CommitmentInstallment).where(CommitmentInstallment.commitment_id.in_(commitment_ids)),
        delete(FinancialCommitment).where(FinancialCommitment.user_id == user_id),
        delete(CreditCardInstallment).where(CreditCardInstallment.purchase_id.in_(purchase_ids)),
        delete(CreditCardPurchase).where(CreditCardPurchase.user_id == user_id),
        delete(CreditCardInvoice).where(CreditCardInvoice.card_id.in_(card_ids)),
        delete(CreditCard).where(CreditCard.user_id == user_id),
        delete(RecurrenceRule).where(RecurrenceRule.user_id == user_id),
        delete(Budget).where(Budget.user_id == user_id),
        delete(FinancialGoal).where(FinancialGoal.user_id == user_id),
        delete(Account).where(Account.user_id == user_id),
        update(Category).where(Category.user_id == user_id).values(parent_id=None),
        delete(Category).where(Category.user_id == user_id),
        delete(FinancialInstitution).where(FinancialInstitution.user_id == user_id),
        delete(RefreshToken).where(RefreshToken.user_id == user_id),
    ]
    for statement in steps:
        db.execute(statement.execution_options(synchronize_session=False))
