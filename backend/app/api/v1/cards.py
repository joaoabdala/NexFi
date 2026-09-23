import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.card import (
    CreditCardCreate,
    CreditCardOut,
    CreditCardPurchaseCreate,
    CreditCardPurchaseOut,
    CreditCardUpdate,
)
from app.schemas.common import MessageResponse
from app.services import card_service, purchase_service
from app.services.card_service import get_card

router = APIRouter()


@router.get("", response_model=list[CreditCardOut])
def list_cards(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return card_service.list_cards(db, current_user.id)


@router.post("", response_model=CreditCardOut, status_code=201)
def create_card(
    payload: CreditCardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return card_service.create_card(db, current_user.id, payload)


@router.get("/{card_id}", response_model=CreditCardOut)
def get_card_detail(
    card_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return card_service.get_card_with_metrics(db, current_user.id, card_id)


@router.put("/{card_id}", response_model=CreditCardOut)
def update_card(
    card_id: uuid.UUID,
    payload: CreditCardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return card_service.update_card(db, current_user.id, card_id, payload)


@router.delete("/{card_id}", response_model=MessageResponse)
def deactivate_card(
    card_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card_service.deactivate_card(db, current_user.id, card_id)
    return MessageResponse(message="Cartão inativado.")


@router.post("/{card_id}/purchases", response_model=CreditCardPurchaseOut, status_code=201)
def create_purchase(
    card_id: uuid.UUID,
    payload: CreditCardPurchaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    purchase = purchase_service.create_purchase(db, current_user.id, card_id, payload)
    metrics = purchase_service.purchase_metrics(db, purchase)
    return {**purchase.__dict__, **metrics}


@router.get("/{card_id}/purchases", response_model=list[CreditCardPurchaseOut])
def list_purchases(
    card_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.repositories import card_repository

    get_card(db, current_user.id, card_id)
    purchases = card_repository.list_purchases_by_card(db, card_id)
    results = []
    for purchase in purchases:
        metrics = purchase_service.purchase_metrics(db, purchase)
        results.append({**purchase.__dict__, **metrics})
    return results
