import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.category import Category
from app.repositories import category_repository
from app.schemas.category import CategoryCreate, CategoryUpdate


def list_categories_tree(db: Session, user_id: uuid.UUID) -> list[Category]:
    categories = category_repository.list_by_user(db, user_id)
    return [c for c in categories if c.parent_id is None]


def get_category(db: Session, user_id: uuid.UUID, category_id: uuid.UUID) -> Category:
    category = category_repository.get_by_id(db, user_id, category_id)
    if not category:
        raise NotFoundError("Categoria não encontrada.")
    return category


def create_category(db: Session, user_id: uuid.UUID, payload: CategoryCreate) -> Category:
    if payload.parent_id is not None:
        parent = category_repository.get_by_id(db, user_id, payload.parent_id)
        if not parent:
            raise ValidationError("Categoria pai inválida.")
        if parent.parent_id is not None:
            raise ValidationError("Não é permitido criar subcategoria de uma subcategoria.")
    category = Category(user_id=user_id, **payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(
    db: Session, user_id: uuid.UUID, category_id: uuid.UUID, payload: CategoryUpdate
) -> Category:
    category = get_category(db, user_id, category_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def deactivate_category(db: Session, user_id: uuid.UUID, category_id: uuid.UUID) -> None:
    category = get_category(db, user_id, category_id)
    category.active = False
    db.add(category)
    db.commit()
