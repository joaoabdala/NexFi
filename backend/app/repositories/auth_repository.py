from datetime import datetime, timezone

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def get_refresh_token_by_hash(db: Session, token_hash: str) -> RefreshToken | None:
    return db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))


def store_refresh_token(db: Session, user_id, token_hash: str, expires_at: datetime) -> RefreshToken:
    record = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    db.add(record)
    db.flush()
    return record


def revoke_refresh_token(db: Session, record: RefreshToken) -> None:
    record.revoked_at = datetime.now(timezone.utc)
    db.add(record)


def delete_dead_refresh_tokens(db: Session, user_id) -> None:
    """Remove tokens revogados ou expirados do usuário — nenhum deles volta a ser aceito, e
    com a rotação a cada refresh a tabela cresceria indefinidamente."""
    # Sem o flush, uma revogação ainda pendente na sessão (autoflush=False) não chega ao banco:
    # o DELETE casa o objeto só em memória, o descarta da sessão, e a linha fica ativa no banco.
    db.flush()
    db.execute(
        delete(RefreshToken).where(
            RefreshToken.user_id == user_id,
            or_(
                RefreshToken.revoked_at.is_not(None),
                RefreshToken.expires_at < datetime.now(timezone.utc),
            ),
        )
    )
