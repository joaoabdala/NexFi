import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import (
    AmortizationType,
    CommitmentInstallmentStatus,
    CommitmentStatus,
    CommitmentType,
)
from app.schemas.common import NonNegativeMoney, ORMModel, PositiveMoney


class FinancialCommitmentCreate(BaseModel):
    institution_id: uuid.UUID
    type: CommitmentType
    name: str = Field(min_length=1, max_length=255)
    asset_value: NonNegativeMoney | None = None
    down_payment: NonNegativeMoney | None = None
    financed_amount: PositiveMoney
    interest_rate: Decimal | None = None
    installments_total: int = Field(ge=1, le=600)
    default_installment_amount: PositiveMoney
    start_date: date
    due_day: int = Field(ge=1, le=31)
    note: str | None = None


class FinancialCommitmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    interest_rate: Decimal | None = None
    status: CommitmentStatus | None = None
    note: str | None = None


class CommitmentInstallmentOut(ORMModel):
    id: uuid.UUID
    commitment_id: uuid.UUID
    number: int
    due_date: date
    original_amount: Decimal
    updated_amount: Decimal
    paid_amount: Decimal | None
    payment_date: date | None
    status: CommitmentInstallmentStatus
    amortization_id: uuid.UUID | None


class FinancialCommitmentOut(ORMModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    type: CommitmentType
    name: str
    asset_value: Decimal | None
    down_payment: Decimal | None
    financed_amount: Decimal
    interest_rate: Decimal | None
    installments_total: int
    default_installment_amount: Decimal
    start_date: date
    due_day: int
    outstanding_balance: Decimal
    status: CommitmentStatus
    note: str | None
    installments_paid: int = 0
    installments_remaining: int = 0
    installments_amortized: int = 0
    total_paid: Decimal = Decimal("0")
    total_amortized: Decimal = Decimal("0")
    accumulated_savings: Decimal = Decimal("0")
    next_installment: CommitmentInstallmentOut | None = None


class InstallmentPayRequest(BaseModel):
    payment_date: date
    account_id: uuid.UUID
    paid_amount: PositiveMoney | None = None


class AmortizationCreate(BaseModel):
    date: date
    paid_amount: PositiveMoney
    type: AmortizationType
    account_id: uuid.UUID
    installment_numbers: list[int] | None = Field(
        default=None,
        description=(
            "Números das parcelas PENDENTES afetadas. Obrigatório para REDUCAO_PRAZO "
            "(parcelas eliminadas). Se omitido em REDUCAO_PARCELA, afeta todas as "
            "parcelas pendentes restantes."
        ),
    )
    note: str | None = None


class AmortizationOut(ORMModel):
    id: uuid.UUID
    commitment_id: uuid.UUID
    date: date
    paid_amount: Decimal
    nominal_amortized_amount: Decimal
    discount_obtained: Decimal
    type: AmortizationType
    account_id: uuid.UUID
    note: str | None
    affected_installment_numbers: list[int] = []
