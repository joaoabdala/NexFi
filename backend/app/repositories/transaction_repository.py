import uuid

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.card import CreditCardInstallment, CreditCardPurchase
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionFilters

SORTABLE_FIELDS = {
    "competence_date": Transaction.competence_date,
    "payment_date": Transaction.payment_date,
    "amount": Transaction.amount,
    "description": Transaction.description,
    "created_at": Transaction.created_at,
}


def _base_query(user_id: uuid.UUID) -> Select:
    return select(Transaction).where(
        Transaction.user_id == user_id, Transaction.deleted_at.is_(None)
    )


def _apply_filters(stmt: Select, filters: TransactionFilters):
    if filters.search:
        stmt = stmt.where(Transaction.description.ilike(f"%{filters.search}%"))
    if filters.date_from:
        stmt = stmt.where(Transaction.competence_date >= filters.date_from)
    if filters.date_to:
        stmt = stmt.where(Transaction.competence_date <= filters.date_to)
    if filters.type:
        stmt = stmt.where(Transaction.type == filters.type)
    if filters.status:
        stmt = stmt.where(Transaction.status == filters.status)
    if filters.category_id:
        stmt = stmt.where(Transaction.category_id == filters.category_id)
    if filters.account_id:
        stmt = stmt.where(Transaction.account_id == filters.account_id)
    if filters.min_amount is not None:
        stmt = stmt.where(Transaction.amount >= filters.min_amount)
    if filters.max_amount is not None:
        stmt = stmt.where(Transaction.amount <= filters.max_amount)
    if filters.institution_id:
        stmt = stmt.join(Account, Account.id == Transaction.account_id).where(
            Account.institution_id == filters.institution_id
        )
    if filters.card_id or filters.payment_mode:
        # outerjoin: transações que não são de cartão têm card_installment_id nulo e devem
        # continuar aparecendo (ex.: contam como "à vista" no filtro payment_mode).
        stmt = stmt.outerjoin(
            CreditCardInstallment, CreditCardInstallment.id == Transaction.card_installment_id
        ).outerjoin(CreditCardPurchase, CreditCardPurchase.id == CreditCardInstallment.purchase_id)
        if filters.card_id:
            stmt = stmt.where(CreditCardPurchase.card_id == filters.card_id)
        if filters.payment_mode == "PARCELADO":
            stmt = stmt.where(CreditCardPurchase.installments_total > 1)
        elif filters.payment_mode == "AVISTA":
            stmt = stmt.where(
                or_(
                    CreditCardPurchase.installments_total.is_(None),
                    CreditCardPurchase.installments_total == 1,
                )
            )
    return stmt


def search(db: Session, user_id: uuid.UUID, filters: TransactionFilters) -> tuple[list[Transaction], int]:
    stmt = _apply_filters(_base_query(user_id), filters)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0

    sort_column = SORTABLE_FIELDS.get(filters.sort_by, Transaction.competence_date)
    order = sort_column.desc() if filters.sort_dir == "desc" else sort_column.asc()
    # Desempate estável: sem isso, transações com a mesma data (ex.: vários lançamentos no
    # mesmo dia) ficam em ordem indefinida pelo SQL — pode variar entre requisições e até
    # embaralhar durante a paginação. created_at desc garante que, entre iguais, o mais
    # recentemente lançado aparece primeiro; id garante unicidade total (nunca há empate).
    stmt = (
        stmt.order_by(order, Transaction.created_at.desc(), Transaction.id)
        .offset((filters.page - 1) * filters.page_size)
        .limit(filters.page_size)
    )

    items = list(db.scalars(stmt))
    return items, total


def get_by_id(db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID) -> Transaction | None:
    stmt = _base_query(user_id).where(Transaction.id == transaction_id)
    return db.scalar(stmt)
