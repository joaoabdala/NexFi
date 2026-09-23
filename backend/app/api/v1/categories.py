import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.schemas.common import MessageResponse
from app.services import category_service

router = APIRouter()


@router.get("", response_model=list[CategoryOut])
def list_categories(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return category_service.list_categories_tree(db, current_user.id)


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(
    payload: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return category_service.create_category(db, current_user.id, payload)


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return category_service.update_category(db, current_user.id, category_id, payload)


@router.delete("/{category_id}", response_model=MessageResponse)
def deactivate_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category_service.deactivate_category(db, current_user.id, category_id)
    return MessageResponse(message="Categoria inativada.")
