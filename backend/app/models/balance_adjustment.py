import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.types import GUID


class BalanceAdjustment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "balance_adjustments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    previous_balance: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    informed_balance: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    difference: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, unique=True
    )
