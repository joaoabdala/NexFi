import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import GoalStatus
from app.schemas.common import ORMModel


class GoalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    target_amount: Decimal
    current_amount: Decimal = Decimal("0")
    linked_account_id: uuid.UUID | None = None
    target_date: date | None = None


class GoalUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    target_amount: Decimal | None = None
    current_amount: Decimal | None = None
    linked_account_id: uuid.UUID | None = None
    target_date: date | None = None
    status: GoalStatus | None = None


class GoalOut(ORMModel):
    id: uuid.UUID
    name: str
    target_amount: Decimal
    current_amount: Decimal
    linked_account_id: uuid.UUID | None
    target_date: date | None
    status: GoalStatus
    progress_percentage: Decimal = Decimal("0")
