import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.types import GUID
from app.models.enums import GoalStatus


class FinancialGoal(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "financial_goals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_amount: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    current_amount: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    linked_account_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[GoalStatus] = mapped_column(
        Enum(GoalStatus, native_enum=False, length=16), default=GoalStatus.EM_ANDAMENTO, nullable=False
    )
