import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.types import GUID
from app.models.enums import RecurrenceFrequency, TransactionType


class RecurrenceRule(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "recurrence_rules"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, native_enum=False, length=32), nullable=False
    )
    amount: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    frequency: Mapped[RecurrenceFrequency] = mapped_column(
        Enum(RecurrenceFrequency, native_enum=False, length=16), nullable=False
    )
    reference_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    custom_interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_generated_competence: Mapped[date | None] = mapped_column(Date, nullable=True)
