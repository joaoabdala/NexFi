import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.category import Category
from app.models.enums import CategoryKind, TransactionStatus, TransactionType
from app.models.financing import CommitmentInstallment
from app.models.transaction import Transaction
from app.repositories import account_repository, category_repository, transaction_repository
from app.schemas.transaction import TransactionCreate, TransactionFilters, TransactionUpdate

RECEITA_LIKE = {TransactionType.RECEITA, TransactionType.RENDIMENTO}
EDITABLE_TYPES = {TransactionType.RECEITA, TransactionType.DESPESA, TransactionType.RENDIMENTO}
# Despesas de compras no cartão têm tipo DESPESA mas são geradas e mantidas pelo módulo de
# cartões (origin="CARTAO") — editá-las ou cancelá-las aqui dessincronizaria a fatura/parcela.
LOCKED_ORIGINS = {"CARTAO"}


def _validate_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> None:
    account = account_repository.get_by_id(db, user_id, account_id)
    if not account:
        raise ValidationError("Conta inválida.")
    if not account.active:
        raise ValidationError("Não é possível lançar movimentações em uma conta inativa.")


def _validate_category(db: Session, user_id: uuid.UUID, category_id: uuid.UUID, txn_type) -> Category:
    category = category_repository.get_by_id(db, user_id, category_id)
    if not category:
        raise ValidationError("Categoria inválida.")
    if not category.active:
        raise ValidationError("Categoria inativa.")
    expected = CategoryKind.RECEITA if txn_type in RECEITA_LIKE else CategoryKind.DESPESA
    if category.kind not in (expected, CategoryKind.AMBOS):
        raise ValidationError(f"Categoria incompatível com o tipo {txn_type.value}.")
    return category


def list_transactions(db: Session, user_id: uuid.UUID, filters: TransactionFilters) -> tuple[list, int]:
    return transaction_repository.search(db, user_id, filters)


def get_transaction(db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID) -> Transaction:
    txn = transaction_repository.get_by_id(db, user_id, transaction_id)
    if not txn:
        raise NotFoundError("Transação não encontrada.")
    return txn


def create_transaction(db: Session, user_id: uuid.UUID, payload: TransactionCreate) -> Transaction:
    _validate_account(db, user_id, payload.account_id)
    if payload.category_id:
        _validate_category(db, user_id, payload.category_id, payload.type)
    if payload.status == TransactionStatus.CONFIRMADA and payload.payment_date is None:
        raise ValidationError("Data de pagamento/recebimento é obrigatória para transações confirmadas.")

    txn = Transaction(
        user_id=user_id,
        origin="MANUAL",
        **payload.model_dump(),
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


REQUIRED_ON_UPDATE = ("account_id", "amount", "description", "competence_date")


def update_transaction(
    db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID, payload: TransactionUpdate
) -> Transaction:
    txn = get_transaction(db, user_id, transaction_id)
    if txn.type not in EDITABLE_TYPES or txn.origin in LOCKED_ORIGINS:
        raise ValidationError(
            "Esta transação foi gerada automaticamente e não pode ser editada diretamente."
        )
    data = payload.model_dump(exclude_unset=True)
    # {"account_id": null} tirava a transação de qualquer saldo (mas ela seguia contando como
    # despesa); {"amount": null} estourava IntegrityError (500).
    cleared = [f for f in REQUIRED_ON_UPDATE if f in data and data[f] is None]
    if cleared:
        raise ValidationError(f"Campo obrigatório não pode ficar vazio: {', '.join(cleared)}.")
    if "account_id" in data and data["account_id"] is not None:
        _validate_account(db, user_id, data["account_id"])
    if "category_id" in data and data["category_id"] is not None:
        _validate_category(db, user_id, data["category_id"], txn.type)
    for field, value in data.items():
        setattr(txn, field, value)
    if txn.status == TransactionStatus.CONFIRMADA and txn.payment_date is None:
        raise ValidationError("Data de pagamento/recebimento é obrigatória para transações confirmadas.")
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def cancel_transaction(db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID) -> Transaction:
    txn = get_transaction(db, user_id, transaction_id)
    if txn.type not in EDITABLE_TYPES or txn.origin in LOCKED_ORIGINS:
        raise ValidationError(
            "Esta transação foi gerada automaticamente e não pode ser cancelada diretamente."
        )
    txn.status = TransactionStatus.CANCELADA
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def reverse_transaction(db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID) -> None:
    """Desfaz um lançamento gerado pelo sistema, delegando ao módulo dono dele — cancelar só a
    transação deixaria a fatura/parcela/outra perna da transferência inconsistente."""
    from app.services import financing_service, invoice_service, transfer_service

    txn = get_transaction(db, user_id, transaction_id)
    if txn.status != TransactionStatus.CONFIRMADA:
        raise ValidationError("Só lançamentos confirmados podem ser desfeitos.")
    if txn.type == TransactionType.TRANSFERENCIA and txn.transfer_id:
        transfer_service.cancel_transfer(db, user_id, txn.transfer_id)
    elif txn.type == TransactionType.PAGAMENTO_FATURA and txn.invoice_id:
        invoice_service.undo_invoice_payment(db, user_id, txn.invoice_id, transaction_id=txn.id)
    elif txn.type == TransactionType.PAGAMENTO_FINANCIAMENTO and txn.commitment_installment_id:
        installment = db.get(CommitmentInstallment, txn.commitment_installment_id)
        if not installment:
            raise ValidationError("Parcela do pagamento não encontrada.")
        financing_service.undo_installment_payment(db, user_id, installment.commitment_id, installment.id)
    else:
        raise ValidationError("Este lançamento não pode ser desfeito por aqui. Use a opção Cancelar.")
