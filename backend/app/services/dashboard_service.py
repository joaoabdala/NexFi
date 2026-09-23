import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.enums import (
    CommitmentInstallmentStatus,
    CommitmentStatus,
    TransactionStatus,
    TransactionType,
)
from app.models.financing import Amortization, CommitmentInstallment, FinancialCommitment
from app.models.transaction import Transaction
from app.repositories import account_repository, card_repository
from app.services.balance_service import get_account_balance, get_card_invoices_due, get_projected_balance
from app.services.card_service import card_metrics as card_with_metrics
from app.services.financing_service import commitment_with_indicators
from app.utils.dates import add_months, month_first_day, local_today
from app.utils.money import quantize, to_decimal


def _month_range(period: str) -> list[tuple[int, int]]:
    today = local_today()
    if period == "3m":
        count = 3
    elif period == "12m":
        count = 12
    elif period == "current_year":
        return [(today.year, m) for m in range(1, today.month + 1)]
    else:
        count = 6
    start = add_months(month_first_day(today.year, today.month), -(count - 1))
    months = []
    cursor = start
    for _ in range(count):
        months.append((cursor.year, cursor.month))
        cursor = add_months(cursor, 1)
    return months


def _sum_by_type_and_month(
    db: Session, user_id: uuid.UUID, txn_type: TransactionType, year: int, month: int
) -> Decimal:
    start = month_first_day(year, month)
    end = add_months(start, 1)
    stmt = select(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.type == txn_type,
        Transaction.status == TransactionStatus.CONFIRMADA,
        Transaction.competence_date >= start,
        Transaction.competence_date < end,
    )
    return quantize(sum((to_decimal(t.amount) for t in db.scalars(stmt)), Decimal("0")))


def _worth_as_of(db: Session, user_id: uuid.UUID, as_of: date) -> tuple[Decimal, Decimal]:
    # Mesmas contas do "saldo disponível" (só ativas) — antes contas desativadas entravam no
    # patrimônio mas não no saldo, e os dois números não batiam.
    accounts = account_repository.list_by_user(db, user_id, active_only=True)
    gross = Decimal("0")
    for account in accounts:
        if not (account.include_in_available_worth or account.include_in_invested_worth):
            continue
        stmt = select(Transaction).where(
            Transaction.account_id == account.id,
            Transaction.status == TransactionStatus.CONFIRMADA,
            Transaction.deleted_at.is_(None),
            # Data em que o dinheiro saiu/entrou da conta, não a competência: um pagamento de
            # fatura feito hoje tem competência no dia 1º do mês da fatura (às vezes no futuro)
            # e sumia do patrimônio de hoje, embora já tivesse saído do saldo.
            func.coalesce(Transaction.payment_date, Transaction.competence_date) <= as_of,
        )
        from app.services.balance_service import _signed_contribution
        from app.models.transfer import Transfer

        transactions = list(db.scalars(stmt))
        transfer_ids = {t.transfer_id for t in transactions if t.transfer_id is not None}
        transfers_by_id = {}
        if transfer_ids:
            transfers_by_id = {
                t.id: t for t in db.scalars(select(Transfer).where(Transfer.id.in_(transfer_ids)))
            }
        balance = to_decimal(account.initial_balance)
        for txn in transactions:
            balance += _signed_contribution(txn, account.id, transfers_by_id)
        gross += balance

    commitments = list(
        db.scalars(
            select(FinancialCommitment).where(
                FinancialCommitment.user_id == user_id,
                FinancialCommitment.status != CommitmentStatus.CANCELADO,
            )
        )
    )
    debt = Decimal("0")
    for commitment in commitments:
        installments = list(
            db.scalars(
                select(CommitmentInstallment).where(
                    CommitmentInstallment.commitment_id == commitment.id
                )
            )
        )
        # Reconstrói o saldo devedor histórico a partir do cronograma (mesma fonte de
        # verdade usada em commitment.outstanding_balance), em vez de derivar de
        # financed_amount — que pode não bater exatamente com parcelas x valor padrão.
        # Uma parcela só deixa de compor a dívida quando sua baixa (pagamento ou
        # amortização) já ocorreu até a data de referência.
        for installment in installments:
            if (
                installment.status == CommitmentInstallmentStatus.PAGA
                and installment.payment_date
                and installment.payment_date <= as_of
            ):
                continue
            if installment.status == CommitmentInstallmentStatus.AMORTIZADA:
                amortization = db.get(Amortization, installment.amortization_id)
                if amortization and amortization.date <= as_of:
                    continue
            debt += to_decimal(installment.updated_amount)

    gross = quantize(gross)
    net = quantize(gross - debt)
    return gross, net


def get_summary(db: Session, user_id: uuid.UUID) -> dict:
    today = local_today()
    accounts = account_repository.list_by_user(db, user_id, active_only=True)
    available_balance = Decimal("0")
    for account in accounts:
        if account.include_in_available_worth:
            available_balance += get_account_balance(db, account)

    income = _sum_by_type_and_month(db, user_id, TransactionType.RECEITA, today.year, today.month)
    expenses = _sum_by_type_and_month(db, user_id, TransactionType.DESPESA, today.year, today.month)
    yield_month = _sum_by_type_and_month(db, user_id, TransactionType.RENDIMENTO, today.year, today.month)
    gross_worth, net_worth = _worth_as_of(db, user_id, today)

    return {
        "available_balance": quantize(available_balance),
        "income_month": income,
        "expenses_month": expenses,
        "result_month": quantize(income - expenses),
        "gross_worth": gross_worth,
        "net_worth": net_worth,
        "yield_month": yield_month,
    }


def get_accounts_summary(db: Session, user_id: uuid.UUID) -> list[dict]:
    accounts = account_repository.list_by_user(db, user_id, active_only=True)
    return [
        {
            "id": a.id,
            "institution_name": a.institution.name if a.institution else "",
            "name": a.name,
            "type": a.type.value,
            "balance": get_account_balance(db, a),
        }
        for a in accounts
    ]


def get_cards_summary(db: Session, user_id: uuid.UUID) -> list[dict]:
    cards = card_repository.list_cards(db, user_id)
    results = []
    for card in cards:
        if not card.active:
            continue
        metrics = card_with_metrics(db, card)
        results.append(
            {
                "id": card.id,
                "name": card.name,
                "current_invoice_amount": metrics["current_invoice_amount"],
                "credit_limit": card.credit_limit,
                "available_limit": metrics["available_limit"],
                "closing_day": card.closing_day,
                "due_day": card.due_day,
            }
        )
    return results


def get_financings_summary(db: Session, user_id: uuid.UUID) -> list[dict]:
    stmt = select(FinancialCommitment).where(
        FinancialCommitment.user_id == user_id, FinancialCommitment.status == CommitmentStatus.ATIVO
    )
    results = []
    for commitment in db.scalars(stmt):
        indicators = commitment_with_indicators(db, commitment)
        next_installment = indicators["next_installment"]
        results.append(
            {
                "id": commitment.id,
                "name": commitment.name,
                "current_installment": indicators["installments_paid"]
                + indicators["installments_amortized"]
                + 1,
                "installments_total": commitment.installments_total,
                "installments_remaining": indicators["installments_remaining"],
                "next_installment_amount": next_installment.updated_amount if next_installment else None,
                "next_installment_due_date": next_installment.due_date if next_installment else None,
                "outstanding_balance": commitment.outstanding_balance,
                "accumulated_savings": indicators["accumulated_savings"],
            }
        )
    return results


def get_income_vs_expenses(db: Session, user_id: uuid.UUID, period: str) -> list[dict]:
    points = []
    for year, month in _month_range(period):
        points.append(
            {
                "label": f"{month:02d}/{year}",
                "year": year,
                "month": month,
                "income": _sum_by_type_and_month(db, user_id, TransactionType.RECEITA, year, month),
                "expenses": _sum_by_type_and_month(db, user_id, TransactionType.DESPESA, year, month),
            }
        )
    return points


def get_expenses_by_category(db: Session, user_id: uuid.UUID, year: int, month: int) -> list[dict]:
    start = month_first_day(year, month)
    end = add_months(start, 1)
    stmt = select(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.DESPESA,
        Transaction.status == TransactionStatus.CONFIRMADA,
        Transaction.competence_date >= start,
        Transaction.competence_date < end,
    )
    totals: dict[uuid.UUID | None, Decimal] = {}
    for txn in db.scalars(stmt):
        totals[txn.category_id] = totals.get(txn.category_id, Decimal("0")) + to_decimal(txn.amount)

    category_ids = [cid for cid in totals if cid is not None]
    categories = {}
    if category_ids:
        categories = {
            c.id: c
            for c in db.scalars(
                select(Category).where(Category.id.in_(category_ids), Category.user_id == user_id)
            )
        }

    return [
        {
            "category_id": cid,
            "category_name": categories[cid].name if cid in categories else "Sem categoria",
            "amount": quantize(amount),
        }
        for cid, amount in sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    ]


def get_worth_evolution(db: Session, user_id: uuid.UUID, period: str) -> list[dict]:
    points = []
    for year, month in _month_range(period):
        month_end = add_months(month_first_day(year, month), 1)
        from datetime import timedelta

        as_of = month_end - timedelta(days=1)
        gross, net = _worth_as_of(db, user_id, as_of)
        points.append(
            {
                "label": f"{month:02d}/{year}",
                "year": year,
                "month": month,
                "gross_worth": gross,
                "net_worth": net,
            }
        )
    return points


def get_yield_evolution(db: Session, user_id: uuid.UUID, period: str) -> list[dict]:
    points = []
    for year, month in _month_range(period):
        points.append(
            {
                "label": f"{month:02d}/{year}",
                "year": year,
                "month": month,
                "yield_amount": _sum_by_type_and_month(
                    db, user_id, TransactionType.RENDIMENTO, year, month
                ),
            }
        )
    return points


def get_yield_by_account(db: Session, user_id: uuid.UUID, year: int, month: int) -> list[dict]:
    start = month_first_day(year, month)
    end = add_months(start, 1)
    stmt = select(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.RENDIMENTO,
        Transaction.status == TransactionStatus.CONFIRMADA,
        Transaction.competence_date >= start,
        Transaction.competence_date < end,
    )
    totals: dict[uuid.UUID, Decimal] = {}
    for txn in db.scalars(stmt):
        if txn.account_id:
            totals[txn.account_id] = totals.get(txn.account_id, Decimal("0")) + to_decimal(txn.amount)

    results = []
    for account_id, amount in totals.items():
        account = account_repository.get_by_id(db, user_id, account_id)
        if not account:
            continue
        results.append(
            {
                "account_id": account_id,
                "account_name": account.name,
                "institution_name": account.institution.name if account.institution else "",
                "amount": quantize(amount),
            }
        )
    return sorted(results, key=lambda r: r["amount"], reverse=True)


def get_projection(db: Session, user_id: uuid.UUID, horizon_days: int) -> dict:
    accounts = account_repository.list_by_user(db, user_id, active_only=True)
    current = Decimal("0")
    projected = Decimal("0")
    card_invoices = Decimal("0")
    limit_date = local_today() + timedelta(days=horizon_days)
    for account in accounts:
        if not account.include_in_available_worth:
            continue
        current += get_account_balance(db, account)
        projected += get_projected_balance(db, account, horizon_days)
        card_invoices += get_card_invoices_due(db, account, limit_date)
    return {
        "horizon_days": horizon_days,
        "current_balance": quantize(current),
        "projected_balance": quantize(projected),
        "card_invoices_due": quantize(card_invoices),
    }


def get_dashboard(db: Session, user_id: uuid.UUID, period: str = "6m") -> dict:
    today = local_today()
    return {
        "summary": get_summary(db, user_id),
        "accounts": get_accounts_summary(db, user_id),
        "cards": get_cards_summary(db, user_id),
        "financings": get_financings_summary(db, user_id),
        "income_vs_expenses": get_income_vs_expenses(db, user_id, period),
        "expenses_by_category": get_expenses_by_category(db, user_id, today.year, today.month),
        "worth_evolution": get_worth_evolution(db, user_id, period),
        "yield_evolution": get_yield_evolution(db, user_id, period),
        "yield_by_account": get_yield_by_account(db, user_id, today.year, today.month),
        "projection_30d": get_projection(db, user_id, 30),
    }
