import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import AccountType
from app.schemas.common import Money, ORMModel


class AccountCreate(BaseModel):
    institution_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    type: AccountType
    initial_balance: Money
    initial_balance_date: date
    active: bool = True
    include_in_available_worth: bool = True
    include_in_invested_worth: bool = False
    note: str | None = None


class AccountUpdate(BaseModel):
    institution_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    type: AccountType | None = None
    active: bool | None = None
    include_in_available_worth: bool | None = None
    include_in_invested_worth: bool | None = None
    note: str | None = None


class AccountOut(ORMModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    name: str
    type: AccountType
    initial_balance: Decimal
    initial_balance_date: date
    active: bool
    include_in_available_worth: bool
    include_in_invested_worth: bool
    note: str | None
    current_balance: Decimal = Decimal("0")
    institution_name: str | None = None


class BalanceAdjustmentCreate(BaseModel):
    informed_balance: Money
    date: date
    note: str | None = None


class BalanceAdjustmentOut(ORMModel):
    id: uuid.UUID
    account_id: uuid.UUID
    previous_balance: Decimal
    informed_balance: Decimal
    difference: Decimal
    date: date
    note: str | None
