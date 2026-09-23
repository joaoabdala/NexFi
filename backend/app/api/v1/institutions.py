import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.institution import InstitutionCreate, InstitutionOut, InstitutionUpdate
from app.services import institution_service

router = APIRouter()


@router.get("", response_model=list[InstitutionOut])
def list_institutions(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list:
    return institution_service.list_institutions(db, current_user.id)


@router.post("", response_model=InstitutionOut, status_code=201)
def create_institution(
    payload: InstitutionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return institution_service.create_institution(db, current_user.id, payload)


@router.get("/{institution_id}", response_model=InstitutionOut)
def get_institution(
    institution_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return institution_service.get_institution(db, current_user.id, institution_id)


@router.put("/{institution_id}", response_model=InstitutionOut)
def update_institution(
    institution_id: uuid.UUID,
    payload: InstitutionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return institution_service.update_institution(db, current_user.id, institution_id, payload)


@router.delete("/{institution_id}", response_model=MessageResponse)
def deactivate_institution(
    institution_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    institution_service.deactivate_institution(db, current_user.id, institution_id)
    return MessageResponse(message="Instituição inativada.")
