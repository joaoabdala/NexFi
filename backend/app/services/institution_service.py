import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.institution import FinancialInstitution
from app.repositories import institution_repository
from app.schemas.institution import InstitutionCreate, InstitutionUpdate


def list_institutions(db: Session, user_id: uuid.UUID) -> list[FinancialInstitution]:
    return institution_repository.list_by_user(db, user_id)


def get_institution(db: Session, user_id: uuid.UUID, institution_id: uuid.UUID) -> FinancialInstitution:
    institution = institution_repository.get_by_id(db, user_id, institution_id)
    if not institution:
        raise NotFoundError("Instituição não encontrada.")
    return institution


def create_institution(
    db: Session, user_id: uuid.UUID, payload: InstitutionCreate
) -> FinancialInstitution:
    institution = FinancialInstitution(user_id=user_id, **payload.model_dump())
    db.add(institution)
    db.commit()
    db.refresh(institution)
    return institution


def update_institution(
    db: Session, user_id: uuid.UUID, institution_id: uuid.UUID, payload: InstitutionUpdate
) -> FinancialInstitution:
    institution = get_institution(db, user_id, institution_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(institution, field, value)
    db.add(institution)
    db.commit()
    db.refresh(institution)
    return institution


def deactivate_institution(db: Session, user_id: uuid.UUID, institution_id: uuid.UUID) -> None:
    institution = get_institution(db, user_id, institution_id)
    institution.active = False
    db.add(institution)
    db.commit()
