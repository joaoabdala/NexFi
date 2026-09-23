"""Regressões de segurança encontradas na auditoria pré-deploy."""

import time
from datetime import date, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import func, select

from app.core.exceptions import UnauthorizedError, ValidationError
from app.core.security import hash_password, verify_password
from app.models.enums import RecurrenceFrequency, TransactionStatus, TransactionType, UserRole
from app.models.refresh_token import RefreshToken
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.admin import AdminUserUpdate
from app.schemas.recurrence import RecurrenceCreate, RecurrenceUpdate
from app.services import admin_user_service, auth_service, recurrence_service
from app.utils.dates import local_today
from tests.conftest import make_category


def _sessions(db, user):
    return db.scalar(select(func.count()).select_from(RefreshToken).where(RefreshToken.user_id == user.id))


# --- Senhas e sessões ---------------------------------------------------------------------------

def test_password_change_revokes_other_sessions_and_keeps_current(db, user):
    """Antes: um refresh token roubado continuava valendo depois da troca de senha."""
    stolen = auth_service.login(db, user.email, "senha12345")
    auth_service.login(db, user.email, "senha12345")  # outro dispositivo

    fresh = auth_service.change_password(db, user, "senha12345", "novaSenha987")

    with pytest.raises(UnauthorizedError):
        auth_service.refresh(db, stolen.refresh_token)
    assert auth_service.refresh(db, fresh.refresh_token).access_token  # esta sessão continua
    assert _sessions(db, user) == 1
    assert auth_service.login(db, user.email, "novaSenha987").access_token


def test_admin_password_reset_and_deactivation_revoke_sessions(db, user):
    admin = User(email="admin@nexfi.app", password_hash=hash_password("senha12345"), name="Admin", role=UserRole.ADMIN)
    db.add(admin)
    db.commit()
    tokens = auth_service.login(db, user.email, "senha12345")

    admin_user_service.update_user(db, user.id, AdminUserUpdate(password="resetada123"))
    with pytest.raises(UnauthorizedError):
        auth_service.refresh(db, tokens.refresh_token)

    tokens = auth_service.login(db, user.email, "resetada123")
    admin_user_service.update_user(db, user.id, AdminUserUpdate(is_active=False))
    assert _sessions(db, user) == 0


def test_passwords_over_72_bytes_are_rejected_by_schema():
    with pytest.raises(PydanticValidationError):
        AdminUserUpdate(password="a" * 73)


def test_login_takes_similar_time_for_unknown_email(db, user):
    """Antes: 180 ms para e-mail existente x 0,2 ms para inexistente (enumeração de contas)."""
    def elapsed(email):
        start = time.perf_counter()
        with pytest.raises(UnauthorizedError):
            auth_service.login(db, email, "senha-errada")
        return time.perf_counter() - start

    known = min(elapsed(user.email) for _ in range(3))
    unknown = min(elapsed("ninguem@nexfi.app") for _ in range(3))
    assert unknown > known * 0.5


def test_verify_password_without_hash_is_false():
    assert verify_password("qualquer", None) is False
    assert verify_password("qualquer", "hash-corrompido") is False


# --- Recorrências -------------------------------------------------------------------------------

def _rule(**overrides):
    data = dict(description="Academia", type=TransactionType.DESPESA, amount=Decimal("100.00"),
                account_id="00000000-0000-0000-0000-000000000001", frequency=RecurrenceFrequency.MENSAL,
                start_date=local_today())
    data.update(overrides)
    return RecurrenceCreate(**data)


def test_recurrence_start_date_older_than_one_year_is_rejected():
    """Antes: início em 2000 + intervalo de 1 dia criava ~10 mil lançamentos numa requisição."""
    with pytest.raises(PydanticValidationError, match="um ano"):
        _rule(start_date=date(2000, 1, 1))
    _rule(start_date=local_today() - timedelta(days=300))  # dentro do limite


def test_recurrence_generation_is_capped_per_call(db, user, account):
    rule = recurrence_service.create_recurrence(
        db, user.id,
        _rule(account_id=account.id, frequency=RecurrenceFrequency.PERSONALIZADA, custom_interval_days=1,
              start_date=local_today() - timedelta(days=365)),
    )
    count = db.scalar(select(func.count()).select_from(Transaction).where(Transaction.recurrence_rule_id == rule.id))
    assert count == recurrence_service.MAX_GENERATED_PER_RULE


def test_monthly_recurrence_from_day_31_does_not_drift_to_28(db, user, account):
    start = date(local_today().year, 1, 31)  # sempre dentro do limite de 1 ano para trás
    rule = recurrence_service.create_recurrence(db, user.id, _rule(account_id=account.id, start_date=start))
    dates = [t.competence_date for t in db.scalars(
        select(Transaction).where(Transaction.recurrence_rule_id == rule.id).order_by(Transaction.competence_date)
    )]
    assert dates[1].day in (28, 29)  # fevereiro
    assert dates[2].day == 31  # março volta para o dia 31 (antes ficava no 28 para sempre)


def test_recurrence_update_rejects_other_users_category(db, user, account):
    other = User(email="outro@nexfi.app", password_hash=hash_password("senha12345"), name="Outro")
    db.add(other)
    db.commit()
    foreign_category = make_category(db, other, name="Categoria do outro")
    rule = recurrence_service.create_recurrence(db, user.id, _rule(account_id=account.id))

    with pytest.raises(ValidationError, match="Categoria inválida"):
        recurrence_service.update_recurrence(db, user.id, rule.id, RecurrenceUpdate(category_id=foreign_category.id))


def test_deleting_recurrence_cancels_its_future_pending_transactions(db, user, account):
    rule = recurrence_service.create_recurrence(db, user.id, _rule(account_id=account.id))
    recurrence_service.delete_recurrence(db, user.id, rule.id)
    statuses = set(db.scalars(select(Transaction.status).where(Transaction.recurrence_rule_id == rule.id)))
    assert statuses == {TransactionStatus.CANCELADA}
