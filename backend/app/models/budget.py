import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.types import GUID


class Budget(UUIDMixin, TimestampMixin, Base):
    """Orçamento por categoria.

    ``month``/``year`` nulos representam o orçamento padrão recorrente da categoria;
    um registro com ``month``/``year`` preenchidos sobrescreve o padrão naquele mês
    específico (ex.: Lazer padrão R$ 500, Lazer dezembro R$ 1.500).
    """

    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint("user_id", "category_id", "month", "year", name="uq_budget_scope"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
