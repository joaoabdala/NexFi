import calendar
from datetime import date


def month_first_day(year: int, month: int) -> date:
    return date(year, month, 1)


def add_months(source: date, months: int) -> date:
    month_index = source.month - 1 + months
    year = source.year + month_index // 12
    month = month_index % 12 + 1
    day = min(source.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def safe_day_in_month(year: int, month: int, day: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last_day))


def invoice_competence_for_purchase(purchase_date: date, closing_day: int) -> date:
    """Determina o mês de competência da fatura para uma compra.

    Se a compra ocorreu no dia do fechamento ou depois, cai na fatura do mês seguinte;
    caso contrário, cai na fatura do mês corrente.
    """
    if purchase_date.day >= closing_day:
        target = add_months(purchase_date, 1)
    else:
        target = purchase_date
    return month_first_day(target.year, target.month)
