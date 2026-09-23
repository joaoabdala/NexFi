import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetOut, BudgetSummaryItem, BudgetUpdate
from app.schemas.common import MessageResponse
from app.services import budget_service
from app.utils.dates import local_today

router = APIRouter()


@router.get("", response_model=list[BudgetOut])
def list_budgets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return budget_service.list_budgets(db, current_user.id)


@router.post("", response_model=BudgetOut, status_code=201)
def create_budget(
    payload: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return budget_service.create_budget(db, current_user.id, payload)


@router.put("/{budget_id}", response_model=BudgetOut)
def update_budget(
    budget_id: uuid.UUID,
    payload: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return budget_service.update_budget(db, current_user.id, budget_id, payload)


@router.delete("/{budget_id}", response_model=MessageResponse)
def delete_budget(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budget_service.delete_budget(db, current_user.id, budget_id)
    return MessageResponse(message="Orçamento removido.")


@router.get("/summary", response_model=list[BudgetSummaryItem])
def get_summary(
    year: int = Query(default_factory=lambda: local_today().year, ge=2000, le=2100),
    month: int = Query(default_factory=lambda: local_today().month, ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return budget_service.get_summary(db, current_user.id, year, month)
