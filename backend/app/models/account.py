import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.types import GUID
from app.models.enums import AccountType


class Account(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("financial_institutions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[AccountType] = mapped_column(
        Enum(AccountType, native_enum=False, length=32), nullable=False
    )
    initial_balance: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    initial_balance_date: Mapped[date] = mapped_column(Date, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    include_in_available_worth: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    include_in_invested_worth: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[date | None] = mapped_column(nullable=True)

    institution: Mapped["FinancialInstitution"] = relationship(back_populates="accounts")  # noqa: F821
