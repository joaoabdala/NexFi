import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.recurrence import RecurrenceCreate, RecurrenceOut, RecurrenceUpdate
from app.services import recurrence_service

router = APIRouter()


@router.get("", response_model=list[RecurrenceOut])
def list_recurrences(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recurrence_service.generate_pending_transactions(db, current_user.id)
    return recurrence_service.list_recurrences(db, current_user.id)


@router.post("", response_model=RecurrenceOut, status_code=201)
def create_recurrence(
    payload: RecurrenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return recurrence_service.create_recurrence(db, current_user.id, payload)


@router.put("/{rule_id}", response_model=RecurrenceOut)
def update_recurrence(
    rule_id: uuid.UUID,
    payload: RecurrenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return recurrence_service.update_recurrence(db, current_user.id, rule_id, payload)


@router.delete("/{rule_id}", response_model=MessageResponse)
def delete_recurrence(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recurrence_service.delete_recurrence(db, current_user.id, rule_id)
    return MessageResponse(message="Recorrência inativada.")


@router.post("/generate", response_model=MessageResponse)
def generate(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count = recurrence_service.generate_pending_transactions(db, current_user.id)
    return MessageResponse(message=f"{count} transação(ões) gerada(s).")
