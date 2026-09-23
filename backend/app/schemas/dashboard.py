import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class SummaryOut(BaseModel):
    available_balance: Decimal
    income_month: Decimal
    expenses_month: Decimal
    result_month: Decimal
    gross_worth: Decimal
    net_worth: Decimal
    yield_month: Decimal


class AccountSummaryOut(BaseModel):
    id: uuid.UUID
    institution_name: str
    name: str
    type: str
    balance: Decimal


class CardSummaryOut(BaseModel):
    id: uuid.UUID
    name: str
    current_invoice_amount: Decimal
    credit_limit: Decimal
    available_limit: Decimal
    closing_day: int
    due_day: int


class FinancingSummaryOut(BaseModel):
    id: uuid.UUID
    name: str
    current_installment: int
    installments_total: int
    installments_remaining: int
    next_installment_amount: Decimal | None
    next_installment_due_date: date | None
    outstanding_balance: Decimal
    accumulated_savings: Decimal


class MonthPoint(BaseModel):
    label: str
    year: int
    month: int
    income: Decimal = Decimal("0")
    expenses: Decimal = Decimal("0")
    gross_worth: Decimal = Decimal("0")
    net_worth: Decimal = Decimal("0")
    yield_amount: Decimal = Decimal("0")


class CategoryExpenseOut(BaseModel):
    category_id: uuid.UUID | None
    category_name: str
    amount: Decimal


class YieldByAccountOut(BaseModel):
    account_id: uuid.UUID
    account_name: str
    institution_name: str
    amount: Decimal


class ProjectionOut(BaseModel):
    horizon_days: int
    current_balance: Decimal
    projected_balance: Decimal


class DashboardOut(BaseModel):
    summary: SummaryOut
    accounts: list[AccountSummaryOut]
    cards: list[CardSummaryOut]
    financings: list[FinancingSummaryOut]
    income_vs_expenses: list[MonthPoint]
    expenses_by_category: list[CategoryExpenseOut]
    worth_evolution: list[MonthPoint]
    yield_evolution: list[MonthPoint]
    yield_by_account: list[YieldByAccountOut]
    projection_30d: ProjectionOut
