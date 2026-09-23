import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.types import GUID
from app.models.enums import InvoiceStatus


class CreditCard(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "credit_cards"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("financial_institutions.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_digits: Mapped[str | None] = mapped_column(String(4), nullable=True)
    credit_limit: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    closing_day: Mapped[int] = mapped_column(Integer, nullable=False)
    due_day: Mapped[int] = mapped_column(Integer, nullable=False)
    default_payment_account_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    invoices: Mapped[list["CreditCardInvoice"]] = relationship(back_populates="card")


class CreditCardInvoice(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "credit_card_invoices"
    __table_args__ = (UniqueConstraint("card_id", "competence", name="uq_invoice_card_competence"),)

    card_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("credit_cards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Primeiro dia do mês de competência da fatura (ex.: 2026-07-01)
    competence: Mapped[date] = mapped_column(Date, nullable=False)
    closing_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, native_enum=False, length=16), default=InvoiceStatus.ABERTA, nullable=False
    )
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_account_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=True
    )
    payment_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True
    )

    card: Mapped["CreditCard"] = relationship(back_populates="invoices")
    installments: Mapped[list["CreditCardInstallment"]] = relationship(back_populates="invoice")


class CreditCardPurchase(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "credit_card_purchases"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    card_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("credit_cards.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    total_amount: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    installments_total: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)

    installments: Mapped[list["CreditCardInstallment"]] = relationship(
        back_populates="purchase", cascade="all, delete-orphan"
    )


class CreditCardInstallment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "credit_card_installments"
    __table_args__ = (
        UniqueConstraint("purchase_id", "number", name="uq_installment_purchase_number"),
    )

    purchase_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("credit_card_purchases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("credit_card_invoices.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[str] = mapped_column(Numeric(15, 2), nullable=False)
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True
    )

    purchase: Mapped["CreditCardPurchase"] = relationship(back_populates="installments")
    invoice: Mapped["CreditCardInvoice"] = relationship(back_populates="installments")
