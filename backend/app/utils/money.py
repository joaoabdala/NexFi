from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")


def to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def quantize(value) -> Decimal:
    return to_decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP)


def split_installments(total: Decimal, count: int) -> list[Decimal]:
    """Divide um valor total em N parcelas, ajustando centavos residuais na última."""
    total = quantize(total)
    base = quantize(total / count)
    installments = [base] * count
    residual = total - (base * count)
    installments[-1] = quantize(installments[-1] + residual)
    return installments
