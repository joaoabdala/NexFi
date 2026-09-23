import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories import financing_repository
from app.schemas.financing import AmortizationCreate, AmortizationOut
from app.services import financing_service
from app.services.financing_service import get_commitment

router = APIRouter()


def _to_out(amortization) -> dict:
    return {
        "id": amortization.id,
        "commitment_id": amortization.commitment_id,
        "date": amortization.date,
        "paid_amount": amortization.paid_amount,
        "nominal_amortized_amount": amortization.nominal_amortized_amount,
        "discount_obtained": amortization.discount_obtained,
        "type": amortization.type,
        "account_id": amortization.account_id,
        "note": amortization.note,
        "affected_installment_numbers": sorted(
            link.commitment_installment.number for link in amortization.affected_installments
        ),
    }


@router.get("/commitments/{commitment_id}", response_model=list[AmortizationOut])
def list_amortizations(
    commitment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    commitment = get_commitment(db, current_user.id, commitment_id)
    amortizations = financing_repository.list_amortizations(db, commitment.id)
    return [_to_out(a) for a in amortizations]


@router.post("/commitments/{commitment_id}", response_model=AmortizationOut, status_code=201)
def create_amortization(
    commitment_id: uuid.UUID,
    payload: AmortizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    amortization = financing_service.create_amortization(db, current_user.id, commitment_id, payload)
    return _to_out(amortization)
