import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import TransactionStatus, TransactionType
from app.schemas.common import ORMModel, PositiveMoney

MANUAL_TYPES = {TransactionType.RECEITA, TransactionType.DESPESA, TransactionType.RENDIMENTO}


class TransactionCreate(BaseModel):
    description: str = Field(min_length=1, max_length=255)
    type: TransactionType
    amount: PositiveMoney
    account_id: uuid.UUID
    category_id: uuid.UUID | None = None
    competence_date: date
    payment_date: date | None = None
    status: TransactionStatus = TransactionStatus.CONFIRMADA
    note: str | None = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("O valor deve ser maior que zero.")
        return value

    @field_validator("type")
    @classmethod
    def type_must_be_manual(cls, value: TransactionType) -> TransactionType:
        if value not in MANUAL_TYPES:
            raise ValueError(
                "Este endpoint aceita apenas RECEITA, DESPESA ou RENDIMENTO. "
                "Transferências, ajustes, faturas e financiamentos possuem fluxos próprios."
            )
        return value


class TransactionUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=255)
    amount: PositiveMoney | None = None
    account_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    competence_date: date | None = None
    payment_date: date | None = None
    status: TransactionStatus | None = None
    note: str | None = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value <= 0:
            raise ValueError("O valor deve ser maior que zero.")
        return value


class TransactionOut(ORMModel):
    id: uuid.UUID
    description: str
    type: TransactionType
    amount: Decimal
    account_id: uuid.UUID | None
    category_id: uuid.UUID | None
    competence_date: date
    payment_date: date | None
    status: TransactionStatus
    note: str | None
    origin: str
    transfer_id: uuid.UUID | None
    invoice_id: uuid.UUID | None
    card_installment_id: uuid.UUID | None
    commitment_installment_id: uuid.UUID | None
    amortization_id: uuid.UUID | None


class TransactionFilters(BaseModel):
    search: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    type: TransactionType | None = None
    status: TransactionStatus | None = None
    category_id: uuid.UUID | None = None
    account_id: uuid.UUID | None = None
    institution_id: uuid.UUID | None = None
    card_id: uuid.UUID | None = None
    payment_mode: Literal["AVISTA", "PARCELADO"] | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    sort_by: str = "competence_date"
    sort_dir: str = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)
