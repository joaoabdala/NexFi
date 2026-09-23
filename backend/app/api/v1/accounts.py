import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.account import (
    AccountCreate,
    AccountOut,
    AccountUpdate,
    BalanceAdjustmentCreate,
    BalanceAdjustmentOut,
)
from app.schemas.common import MessageResponse
from app.services import account_service

router = APIRouter()


@router.get("", response_model=list[AccountOut])
def list_accounts(
    active_only: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return account_service.list_accounts(db, current_user.id, active_only)


@router.post("", response_model=AccountOut, status_code=201)
def create_account(
    payload: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return account_service.create_account(db, current_user.id, payload)


@router.get("/{account_id}", response_model=AccountOut)
def get_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return account_service.get_account_with_balance(db, current_user.id, account_id)


@router.put("/{account_id}", response_model=AccountOut)
def update_account(
    account_id: uuid.UUID,
    payload: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return account_service.update_account(db, current_user.id, account_id, payload)


@router.delete("/{account_id}", response_model=MessageResponse)
def deactivate_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account_service.deactivate_account(db, current_user.id, account_id)
    return MessageResponse(message="Conta inativada.")


@router.post("/{account_id}/balance-adjustments", response_model=BalanceAdjustmentOut, status_code=201)
def create_balance_adjustment(
    account_id: uuid.UUID,
    payload: BalanceAdjustmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return account_service.create_balance_adjustment(db, current_user.id, account_id, payload)
