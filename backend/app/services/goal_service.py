import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.enums import GoalStatus
from app.models.goal import FinancialGoal
from app.repositories import account_repository
from app.schemas.goal import GoalCreate, GoalUpdate
from app.services.balance_service import get_account_balance
from app.utils.money import quantize, to_decimal


def _with_progress(db: Session, goal: FinancialGoal) -> dict:
    current = to_decimal(goal.current_amount)
    if goal.linked_account_id:
        account = account_repository.get_by_id(db, goal.user_id, goal.linked_account_id)
        if account:
            current = get_account_balance(db, account)
    target = to_decimal(goal.target_amount)
    percentage = quantize((current / target * 100) if target else Decimal("0"))
    return {
        "id": goal.id,
        "name": goal.name,
        "target_amount": goal.target_amount,
        "current_amount": current,
        "linked_account_id": goal.linked_account_id,
        "target_date": goal.target_date,
        "status": goal.status,
        "progress_percentage": percentage,
    }


def list_goals(db: Session, user_id: uuid.UUID) -> list[dict]:
    stmt = select(FinancialGoal).where(FinancialGoal.user_id == user_id).order_by(FinancialGoal.name)
    return [_with_progress(db, g) for g in db.scalars(stmt)]


def get_goal(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID) -> FinancialGoal:
    stmt = select(FinancialGoal).where(FinancialGoal.id == goal_id, FinancialGoal.user_id == user_id)
    goal = db.scalar(stmt)
    if not goal:
        raise NotFoundError("Meta não encontrada.")
    return goal


def create_goal(db: Session, user_id: uuid.UUID, payload: GoalCreate) -> dict:
    if payload.linked_account_id and not account_repository.get_by_id(
        db, user_id, payload.linked_account_id
    ):
        raise ValidationError("Conta vinculada inválida.")
    goal = FinancialGoal(user_id=user_id, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return _with_progress(db, goal)


def update_goal(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID, payload: GoalUpdate) -> dict:
    goal = get_goal(db, user_id, goal_id)
    data = payload.model_dump(exclude_unset=True)
    if data.get("linked_account_id") and not account_repository.get_by_id(
        db, user_id, data["linked_account_id"]
    ):
        raise ValidationError("Conta vinculada inválida.")
    for field, value in data.items():
        setattr(goal, field, value)
    if goal.status is None:
        goal.status = GoalStatus.EM_ANDAMENTO
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return _with_progress(db, goal)


def delete_goal(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID) -> None:
    goal = get_goal(db, user_id, goal_id)
    db.delete(goal)
    db.commit()
