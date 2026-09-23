import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.types import GUID
from app.models.enums import TransactionStatus, TransactionType


class Transaction(UUIDMixin, TimestampMixin, Base):
    """Registro central de movimentação financeira.

    ``account_id`` é nulo apenas para compras no cartão de crédito ainda não pagas
    (a despesa existe por competência, mas não debita conta nenhuma até o
    pagamento da fatura — ver Transaction.type == PAGAMENTO_FATURA).
    """

    __tablename__ = "transactions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, native_enum=False, length=32), nullable=False, index=True
    )
    amount: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    competence_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, native_enum=False, length=16),
        nullable=False,
        default=TransactionStatus.CONFIRMADA,
        index=True,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    origin: Mapped[str] = mapped_column(String(32), nullable=False, default="MANUAL")
    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    transfer_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("transfers.id", ondelete="CASCADE"), nullable=True, index=True
    )
    card_installment_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("credit_card_installments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("credit_card_invoices.id", ondelete="SET NULL"), nullable=True, index=True
    )
    commitment_installment_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("commitment_installments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    amortization_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("amortizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    recurrence_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("recurrence_rules.id", ondelete="SET NULL"), nullable=True, index=True
    )

    deleted_at: Mapped[date | None] = mapped_column(nullable=True)
