import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.types import GUID
from app.models.enums import (
    AmortizationType,
    CommitmentInstallmentStatus,
    CommitmentStatus,
    CommitmentType,
)


class FinancialCommitment(UUIDMixin, TimestampMixin, Base):
    """Generaliza financiamento / empréstimo / consórcio (Financial Commitment)."""

    __tablename__ = "financial_commitments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("financial_institutions.id", ondelete="RESTRICT"), nullable=False
    )
    type: Mapped[CommitmentType] = mapped_column(
        Enum(CommitmentType, native_enum=False, length=16), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_value: Mapped[str | None] = mapped_column(Numeric(15, 2), nullable=True)
    down_payment: Mapped[str | None] = mapped_column(Numeric(15, 2), nullable=True)
    financed_amount: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    interest_rate: Mapped[str | None] = mapped_column(Numeric(9, 6), nullable=True)
    installments_total: Mapped[int] = mapped_column(Integer, nullable=False)
    default_installment_amount: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_day: Mapped[int] = mapped_column(Integer, nullable=False)
    outstanding_balance: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[CommitmentStatus] = mapped_column(
        Enum(CommitmentStatus, native_enum=False, length=16),
        default=CommitmentStatus.ATIVO,
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    installments: Mapped[list["CommitmentInstallment"]] = relationship(back_populates="commitment")


class CommitmentInstallment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "commitment_installments"
    __table_args__ = (
        UniqueConstraint("commitment_id", "number", name="uq_commitment_installment_number"),
    )

    commitment_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("financial_commitments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    original_amount: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    updated_amount: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    paid_amount: Mapped[str | None] = mapped_column(Numeric(15, 2), nullable=True)
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[CommitmentInstallmentStatus] = mapped_column(
        Enum(CommitmentInstallmentStatus, native_enum=False, length=16),
        default=CommitmentInstallmentStatus.PENDENTE,
        nullable=False,
    )
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True
    )
    amortization_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("amortizations.id", ondelete="SET NULL"), nullable=True
    )

    commitment: Mapped["FinancialCommitment"] = relationship(back_populates="installments")


class Amortization(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "amortizations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    commitment_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("financial_commitments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_amount: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    nominal_amortized_amount: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    discount_obtained: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    type: Mapped[AmortizationType] = mapped_column(
        Enum(AmortizationType, native_enum=False, length=32), nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True
    )

    affected_installments: Mapped[list["AmortizationInstallment"]] = relationship(
        back_populates="amortization", cascade="all, delete-orphan"
    )


class AmortizationInstallment(UUIDMixin, Base):
    """Associação N:N explícita: rastreia exatamente quais parcelas cada amortização afetou."""

    __tablename__ = "amortization_installments"
    __table_args__ = (
        UniqueConstraint(
            "amortization_id", "commitment_installment_id", name="uq_amortization_installment"
        ),
    )

    amortization_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("amortizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    commitment_installment_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("commitment_installments.id", ondelete="CASCADE"), nullable=False, index=True
    )

    amortization: Mapped["Amortization"] = relationship(back_populates="affected_installments")
    commitment_installment: Mapped["CommitmentInstallment"] = relationship()
