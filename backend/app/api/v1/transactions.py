import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import TransactionStatus, TransactionType
from app.models.user import User
from app.schemas.common import MessageResponse, Page
from app.schemas.transaction import (
    TransactionCreate,
    TransactionFilters,
    TransactionOut,
    TransactionUpdate,
)
from app.services import transaction_service

router = APIRouter()


@router.get("", response_model=Page[TransactionOut])
def list_transactions(
    search: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    type: TransactionType | None = None,
    status: TransactionStatus | None = None,
    category_id: uuid.UUID | None = None,
    account_id: uuid.UUID | None = None,
    institution_id: uuid.UUID | None = None,
    card_id: uuid.UUID | None = None,
    payment_mode: Literal["AVISTA", "PARCELADO"] | None = None,
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
    sort_by: str = "competence_date",
    sort_dir: str = "desc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filters = TransactionFilters(
        search=search,
        date_from=date_from,
        date_to=date_to,
        type=type,
        status=status,
        category_id=category_id,
        account_id=account_id,
        institution_id=institution_id,
        card_id=card_id,
        payment_mode=payment_mode,
        min_amount=min_amount,
        max_amount=max_amount,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )
    items, total = transaction_service.list_transactions(db, current_user.id, filters)
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=TransactionOut, status_code=201)
def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return transaction_service.create_transaction(db, current_user.id, payload)


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return transaction_service.get_transaction(db, current_user.id, transaction_id)


@router.put("/{transaction_id}", response_model=TransactionOut)
def update_transaction(
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return transaction_service.update_transaction(db, current_user.id, transaction_id, payload)


@router.delete("/{transaction_id}", response_model=MessageResponse)
def cancel_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transaction_service.cancel_transaction(db, current_user.id, transaction_id)
    return MessageResponse(message="Transação cancelada.")


@router.post("/{transaction_id}/reverse", response_model=MessageResponse)
def reverse_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Desfaz transferência, pagamento de fatura ou pagamento de parcela a partir do lançamento."""
    transaction_service.reverse_transaction(db, current_user.id, transaction_id)
    return MessageResponse(message="Lançamento desfeito.")
