import pytest

from app.core.exceptions import ConflictError, ValidationError
from app.models.enums import UserRole
from app.schemas.admin import AdminUserCreate, AdminUserUpdate
from app.services import admin_user_service


def _make_admin(db, user):
    user.role = UserRole.ADMIN
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_admin_can_create_and_list_users(db, user):
    _make_admin(db, user)
    created = admin_user_service.create_user(
        db,
        AdminUserCreate(email="novo@nexfi.app", password="senha12345", name="Novo Usuário"),
    )
    assert created.role == UserRole.USER
    assert created.is_active is True

    users = admin_user_service.list_users(db)
    emails = {u.email for u in users}
    assert "novo@nexfi.app" in emails


def test_cannot_create_user_with_duplicate_email(db, user):
    _make_admin(db, user)
    with pytest.raises(ConflictError):
        admin_user_service.create_user(
            db, AdminUserCreate(email=user.email, password="senha12345", name="Duplicado")
        )


def test_admin_cannot_delete_self(db, user):
    admin = _make_admin(db, user)
    with pytest.raises(ValidationError):
        admin_user_service.delete_user(db, admin, admin.id)


def test_cannot_demote_last_active_admin(db, user):
    admin = _make_admin(db, user)
    with pytest.raises(ValidationError):
        admin_user_service.update_user(db, admin.id, AdminUserUpdate(role=UserRole.USER))


def test_cannot_delete_last_active_admin(db, user):
    admin = _make_admin(db, user)
    other_admin = admin_user_service.create_user(
        db,
        AdminUserCreate(email="segundo@nexfi.app", password="senha12345", name="Segundo Admin", role=UserRole.ADMIN),
    )
    # Com dois admins ativos, é possível rebaixar/excluir um deles.
    admin_user_service.delete_user(db, admin, other_admin.id)
    # Agora só resta um admin ativo — não pode mais ser removido.
    with pytest.raises(ValidationError):
        admin_user_service.update_user(db, admin.id, AdminUserUpdate(is_active=False))
