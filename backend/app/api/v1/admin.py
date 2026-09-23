import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import AdminUserCreate, AdminUserOut, AdminUserUpdate
from app.schemas.common import MessageResponse
from app.services import admin_user_service

router = APIRouter()


@router.get("/users", response_model=list[AdminUserOut])
def list_users(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    return admin_user_service.list_users(db)


@router.post("/users", response_model=AdminUserOut, status_code=201)
def create_user(
    payload: AdminUserCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    return admin_user_service.create_user(db, payload)


@router.put("/users/{user_id}", response_model=AdminUserOut)
def update_user(
    user_id: uuid.UUID,
    payload: AdminUserUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    return admin_user_service.update_user(db, user_id, payload)


@router.delete("/users/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: uuid.UUID,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    admin_user_service.delete_user(db, current_admin, user_id)
    return MessageResponse(message="Usuário excluído.")
