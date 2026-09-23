import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.types import GUID


class Transfer(UUIDMixin, TimestampMixin, Base):
    """Registro lógico de uma transferência entre contas do mesmo usuário.

    Gera duas ``Transaction`` (tipo TRANSFERENCIA) vinculadas por ``transfer_id``,
    nunca uma receita/despesa isolada.
    """

    __tablename__ = "transfers"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_account_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    to_account_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    amount: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
