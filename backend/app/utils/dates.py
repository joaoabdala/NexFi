import calendar
from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.core.config import settings


def local_today() -> date:
    """Data de hoje no fuso da aplicação (America/Sao_Paulo por padrão).

    Não usar ``date.today()``: na Vercel o servidor roda em UTC, e a partir das 21h no Brasil
    isso já é o dia seguinte — faturas apareceriam vencidas no próprio dia do vencimento e o
    dashboard viraria o mês antes da hora no último dia.
    """
    return datetime.now(ZoneInfo(settings.APP_TIMEZONE)).date()


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
    caso contrário, cai na fatura do mês corrente. O fechamento é ajustado ao tamanho do mês
    (dia 31 em fevereiro fecha no dia 28/29), igual à data de fechamento da própria fatura.
    """
    closing_date = safe_day_in_month(purchase_date.year, purchase_date.month, closing_day)
    if purchase_date >= closing_date:
        target = add_months(purchase_date, 1)
    else:
        target = purchase_date
    return month_first_day(target.year, target.month)
