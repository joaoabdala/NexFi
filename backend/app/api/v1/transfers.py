import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.transfer import TransferCreate, TransferOut
from app.services import transfer_service

router = APIRouter()


@router.get("", response_model=list[TransferOut])
def list_transfers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return transfer_service.list_transfers(db, current_user.id)


@router.post("", response_model=TransferOut, status_code=201)
def create_transfer(
    payload: TransferCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return transfer_service.create_transfer(db, current_user.id, payload)


@router.get("/{transfer_id}", response_model=TransferOut)
def get_transfer(
    transfer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return transfer_service.get_transfer(db, current_user.id, transfer_id)


@router.post("/{transfer_id}/cancel", response_model=TransferOut)
def cancel_transfer(
    transfer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Desfaz a transferência (os saldos das duas contas voltam ao que eram)."""
    return transfer_service.cancel_transfer(db, current_user.id, transfer_id)
