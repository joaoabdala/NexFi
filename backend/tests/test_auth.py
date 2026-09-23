from app.services import auth_service


def test_login_then_refresh_roundtrip_does_not_crash(db, user):
    """Regressão: expires_at lido do banco (naive no SQLite) comparado com um datetime
    timezone-aware crashava o endpoint de refresh com TypeError, derrubando a sessão do
    usuário silenciosamente a cada expiração do access token (a cada poucos minutos)."""
    tokens = auth_service.login(db, user.email, "senha12345")
    assert tokens.access_token
    assert tokens.refresh_token

    refreshed = auth_service.refresh(db, tokens.refresh_token)
    assert refreshed.access_token
    assert refreshed.refresh_token
    assert refreshed.refresh_token != tokens.refresh_token


def test_refresh_token_is_rotated_and_old_one_is_rejected(db, user):
    tokens = auth_service.login(db, user.email, "senha12345")
    auth_service.refresh(db, tokens.refresh_token)

    import pytest

    from app.core.exceptions import UnauthorizedError

    with pytest.raises(UnauthorizedError):
        auth_service.refresh(db, tokens.refresh_token)


def test_refresh_chain_can_be_used_many_times_in_sequence(db, user):
    """Simula uso contínuo do app: cada expiração do access token dispara um refresh —
    isso precisa funcionar indefinidamente, não só na primeira vez."""
    tokens = auth_service.login(db, user.email, "senha12345")
    for _ in range(5):
        tokens = auth_service.refresh(db, tokens.refresh_token)
    assert tokens.access_token


def test_dead_refresh_tokens_are_purged_on_issue(db, user):
    """Com rotação a cada refresh (a cada ~15 min de uso), tokens revogados/expirados
    acumulariam para sempre — importante no limite de 500 MB do Neon Free."""
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import select

    from app.core.security import hash_refresh_token
    from app.models.refresh_token import RefreshToken
    from app.repositories import auth_repository

    other_session = auth_service.login(db, user.email, "senha12345")  # outro dispositivo, válido
    expired_hash = hash_refresh_token("expirado")
    auth_repository.store_refresh_token(
        db, user.id, expired_hash, datetime.now(timezone.utc) - timedelta(days=1)
    )
    db.commit()

    tokens = auth_service.login(db, user.email, "senha12345")
    for _ in range(5):
        tokens = auth_service.refresh(db, tokens.refresh_token)

    hashes = set(db.scalars(select(RefreshToken.token_hash).where(RefreshToken.user_id == user.id)))
    assert hashes == {
        hash_refresh_token(other_session.refresh_token),
        hash_refresh_token(tokens.refresh_token),
    }
    assert expired_hash not in hashes
