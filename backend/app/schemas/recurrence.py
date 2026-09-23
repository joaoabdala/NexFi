import uuid
from datetime import date, timedelta
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import RecurrenceFrequency, TransactionType
from app.schemas.common import ORMModel, PositiveMoney
from app.utils.dates import local_today

RECURRENCE_TYPES = {TransactionType.RECEITA, TransactionType.DESPESA}


class RecurrenceCreate(BaseModel):
    description: str = Field(min_length=1, max_length=255)
    type: TransactionType
    amount: PositiveMoney
    account_id: uuid.UUID
    category_id: uuid.UUID | None = None
    frequency: RecurrenceFrequency
    reference_day: int | None = Field(default=None, ge=1, le=31)
    custom_interval_days: int | None = Field(default=None, ge=1)
    start_date: date
    end_date: date | None = None
    active: bool = True

    @field_validator("type")
    @classmethod
    def type_must_be_receita_or_despesa(cls, value: TransactionType) -> TransactionType:
        if value not in RECURRENCE_TYPES:
            raise ValueError("Recorrências aceitam apenas RECEITA ou DESPESA.")
        return value

    @field_validator("amount")
    @classmethod
    def positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("O valor deve ser maior que zero.")
        return value

    @field_validator("start_date")
    @classmethod
    def start_date_within_one_year_back(cls, value: date) -> date:
        # Uma data inicial muito antiga gera um lançamento pendente para cada ocorrência
        # passada — com intervalo de 1 dia desde 2000, eram ~10 mil linhas numa requisição.
        if value < local_today() - timedelta(days=366):
            raise ValueError("A data inicial não pode ser anterior a um ano atrás.")
        return value


class RecurrenceUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=255)
    amount: PositiveMoney | None = None
    category_id: uuid.UUID | None = None
    active: bool | None = None
    end_date: date | None = None


class RecurrenceOut(ORMModel):
    id: uuid.UUID
    description: str
    type: TransactionType
    amount: Decimal
    account_id: uuid.UUID
    category_id: uuid.UUID | None
    frequency: RecurrenceFrequency
    reference_day: int | None
    start_date: date
    end_date: date | None
    active: bool
    last_generated_competence: date | None
