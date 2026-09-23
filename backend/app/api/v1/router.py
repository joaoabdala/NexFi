from fastapi import APIRouter

from app.api.v1 import (
    accounts,
    admin,
    amortizations,
    auth,
    budgets,
    cards,
    categories,
    dashboard,
    financing,
    goals,
    institutions,
    invoices,
    recurrences,
    transactions,
    transfers,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(institutions.router, prefix="/institutions", tags=["institutions"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(transfers.router, prefix="/transfers", tags=["transfers"])
api_router.include_router(cards.router, prefix="/cards", tags=["cards"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
api_router.include_router(financing.router, prefix="/financing", tags=["financing"])
api_router.include_router(amortizations.router, prefix="/amortizations", tags=["amortizations"])
api_router.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])
api_router.include_router(recurrences.router, prefix="/recurrences", tags=["recurrences"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
