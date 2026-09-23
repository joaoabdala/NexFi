import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories import financing_repository
from app.schemas.financing import (
    CommitmentInstallmentOut,
    FinancialCommitmentCreate,
    FinancialCommitmentOut,
    FinancialCommitmentUpdate,
    InstallmentPayRequest,
)
from app.services import financing_service
from app.services.financing_service import get_commitment

router = APIRouter()


@router.get("", response_model=list[FinancialCommitmentOut])
def list_commitments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return financing_service.list_commitments(db, current_user.id)


@router.post("", response_model=FinancialCommitmentOut, status_code=201)
def create_commitment(
    payload: FinancialCommitmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return financing_service.create_commitment(db, current_user.id, payload)


@router.get("/{commitment_id}", response_model=FinancialCommitmentOut)
def get_commitment_detail(
    commitment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return financing_service.get_commitment_with_indicators(db, current_user.id, commitment_id)


@router.put("/{commitment_id}", response_model=FinancialCommitmentOut)
def update_commitment(
    commitment_id: uuid.UUID,
    payload: FinancialCommitmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return financing_service.update_commitment(db, current_user.id, commitment_id, payload)


@router.get("/{commitment_id}/installments", response_model=list[CommitmentInstallmentOut])
def list_installments(
    commitment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    commitment = get_commitment(db, current_user.id, commitment_id)
    return financing_repository.list_installments(db, commitment.id)


@router.post(
    "/{commitment_id}/installments/{installment_id}/pay", response_model=CommitmentInstallmentOut
)
def pay_installment(
    commitment_id: uuid.UUID,
    installment_id: uuid.UUID,
    payload: InstallmentPayRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return financing_service.pay_installment(db, current_user.id, commitment_id, installment_id, payload)


@router.post(
    "/{commitment_id}/installments/{installment_id}/undo-payment", response_model=CommitmentInstallmentOut
)
def undo_installment_payment(
    commitment_id: uuid.UUID,
    installment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Desfaz o pagamento da parcela (o valor volta para a conta e a parcela fica pendente)."""
    return financing_service.undo_installment_payment(db, current_user.id, commitment_id, installment_id)
