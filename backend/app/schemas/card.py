import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import InvoiceStatus
from app.schemas.common import NonNegativeMoney, ORMModel, PositiveMoney


class CreditCardCreate(BaseModel):
    institution_id: uuid.UUID
    name: str = Field(min_length=1, max_length=120)
    brand: str | None = Field(default=None, max_length=32)
    last_digits: str | None = Field(default=None, max_length=4)
    credit_limit: NonNegativeMoney
    closing_day: int = Field(ge=1, le=31)
    due_day: int = Field(ge=1, le=31)
    default_payment_account_id: uuid.UUID
    active: bool = True


class CreditCardUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    brand: str | None = None
    last_digits: str | None = None
    credit_limit: NonNegativeMoney | None = None
    closing_day: int | None = Field(default=None, ge=1, le=31)
    due_day: int | None = Field(default=None, ge=1, le=31)
    default_payment_account_id: uuid.UUID | None = None
    active: bool | None = None


class CreditCardOut(ORMModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    name: str
    brand: str | None
    last_digits: str | None
    credit_limit: Decimal
    closing_day: int
    due_day: int
    default_payment_account_id: uuid.UUID
    active: bool
    current_invoice_amount: Decimal = Decimal("0")
    available_limit: Decimal = Decimal("0")


class CreditCardInstallmentOut(ORMModel):
    id: uuid.UUID
    purchase_id: uuid.UUID
    invoice_id: uuid.UUID
    number: int
    amount: Decimal
    description: str | None = None
    installments_total: int | None = None


class CreditCardInvoiceOut(ORMModel):
    id: uuid.UUID
    card_id: uuid.UUID
    competence: date
    closing_date: date
    due_date: date
    status: InvoiceStatus
    amount: Decimal = Decimal("0")
    paid_amount: Decimal = Decimal("0")
    payment_date: date | None
    payment_account_id: uuid.UUID | None
    installments: list[CreditCardInstallmentOut] = []


class InvoiceProjectionCard(BaseModel):
    id: uuid.UUID
    name: str


class InvoiceProjectionMonth(BaseModel):
    year: int
    month: int
    total: Decimal
    by_card: dict[str, Decimal]


class InvoiceProjectionOut(BaseModel):
    cards: list[InvoiceProjectionCard]
    months: list[InvoiceProjectionMonth]


class CreditCardPurchaseCreate(BaseModel):
    description: str = Field(min_length=1, max_length=255)
    total_amount: PositiveMoney
    installments_total: int = Field(default=1, ge=1, le=60)
    purchase_date: date
    category_id: uuid.UUID | None = None

    @field_validator("total_amount")
    @classmethod
    def positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("O valor deve ser maior que zero.")
        return value


class CreditCardPurchaseOut(ORMModel):
    id: uuid.UUID
    card_id: uuid.UUID
    description: str
    total_amount: Decimal
    installments_total: int
    purchase_date: date
    category_id: uuid.UUID | None
    invoiced_amount: Decimal = Decimal("0")
    future_amount: Decimal = Decimal("0")
    installments_remaining: int = 0


class InvoicePayRequest(BaseModel):
    payment_date: date
    payment_account_id: uuid.UUID | None = None
