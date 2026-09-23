import uuid
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class BudgetCreate(BaseModel):
    category_id: uuid.UUID
    amount: Decimal
    month: int | None = Field(default=None, ge=1, le=12)
    year: int | None = Field(default=None, ge=2000, le=2100)


class BudgetUpdate(BaseModel):
    amount: Decimal


class BudgetOut(ORMModel):
    id: uuid.UUID
    category_id: uuid.UUID
    amount: Decimal
    month: int | None
    year: int | None
    is_default: bool


class BudgetSummaryItem(BaseModel):
    category_id: uuid.UUID
    category_name: str
    budget_amount: Decimal
    realized_amount: Decimal
    remaining_amount: Decimal
    percentage_used: Decimal
