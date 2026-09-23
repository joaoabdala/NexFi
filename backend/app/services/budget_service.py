import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.budget import Budget
from app.models.category import Category
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.repositories import budget_repository, category_repository
from app.schemas.budget import BudgetCreate, BudgetUpdate
from app.utils.money import quantize, to_decimal


def list_budgets(db: Session, user_id: uuid.UUID) -> list[Budget]:
    return budget_repository.list_by_user(db, user_id)


def create_budget(db: Session, user_id: uuid.UUID, payload: BudgetCreate) -> Budget:
    category = category_repository.get_by_id(db, user_id, payload.category_id)
    if not category:
        raise ValidationError("Categoria inválida.")
    if (payload.month is None) != (payload.year is None):
        raise ValidationError("Informe mês e ano juntos, ou nenhum dos dois (orçamento padrão).")
    existing = budget_repository.get_scoped(db, user_id, payload.category_id, payload.month, payload.year)
    if existing:
        raise ConflictError("Já existe um orçamento para esta categoria neste escopo.")

    budget = Budget(
        user_id=user_id,
        category_id=payload.category_id,
        amount=payload.amount,
        month=payload.month,
        year=payload.year,
        is_default=payload.month is None,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def update_budget(db: Session, user_id: uuid.UUID, budget_id: uuid.UUID, payload: BudgetUpdate) -> Budget:
    budget = budget_repository.get_by_id(db, user_id, budget_id)
    if not budget:
        raise NotFoundError("Orçamento não encontrado.")
    budget.amount = payload.amount
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def delete_budget(db: Session, user_id: uuid.UUID, budget_id: uuid.UUID) -> None:
    budget = budget_repository.get_by_id(db, user_id, budget_id)
    if not budget:
        raise NotFoundError("Orçamento não encontrado.")
    db.delete(budget)
    db.commit()


def get_summary(db: Session, user_id: uuid.UUID, year: int, month: int) -> list[dict]:
    budgets = budget_repository.list_by_user(db, user_id)
    effective: dict[uuid.UUID, Budget] = {}
    for budget in budgets:
        if budget.month is None and budget.category_id not in effective:
            effective[budget.category_id] = budget
    for budget in budgets:
        if budget.month == month and budget.year == year:
            effective[budget.category_id] = budget

    if not effective:
        return []

    category_ids = list(effective.keys())
    categories = {
        c.id: c
        for c in db.scalars(select(Category).where(Category.id.in_(category_ids)))
    }

    period_start = date(year, month, 1)
    period_end = date(year + (1 if month == 12 else 0), 1 if month == 12 else month + 1, 1)

    # Orçamentos são definidos por categoria principal, mas transações costumam ser
    # lançadas na subcategoria (ex.: "Mercado" dentro de "Alimentação") — o realizado
    # precisa somar a categoria e todas as suas subcategorias.
    all_categories = db.scalars(select(Category).where(Category.user_id == user_id)).all()
    children_by_parent: dict[uuid.UUID, list[uuid.UUID]] = {}
    for c in all_categories:
        if c.parent_id:
            children_by_parent.setdefault(c.parent_id, []).append(c.id)

    results = []
    for category_id, budget in effective.items():
        scoped_ids = [category_id, *children_by_parent.get(category_id, [])]
        stmt = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.category_id.in_(scoped_ids),
            Transaction.type == TransactionType.DESPESA,
            Transaction.status == TransactionStatus.CONFIRMADA,
            Transaction.competence_date >= period_start,
            Transaction.competence_date < period_end,
        )
        realized = quantize(sum((to_decimal(t.amount) for t in db.scalars(stmt)), Decimal("0")))
        budget_amount = to_decimal(budget.amount)
        remaining = quantize(budget_amount - realized)
        percentage = quantize((realized / budget_amount * 100) if budget_amount else Decimal("0"))
        category = categories.get(category_id)
        results.append(
            {
                "category_id": category_id,
                "category_name": category.name if category else "",
                "budget_amount": budget_amount,
                "realized_amount": realized,
                "remaining_amount": remaining,
                "percentage_used": percentage,
            }
        )
    return results
