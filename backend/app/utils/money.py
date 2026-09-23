from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")


def to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def quantize(value) -> Decimal:
    return to_decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP)


def split_installments(total: Decimal, count: int) -> list[Decimal]:
    """Divide um valor total em N parcelas que somam exatamente o total.

    A base é arredondada para BAIXO e os centavos que sobram vão, um a um, para as últimas
    parcelas (1000/3 → 333,33 + 333,33 + 333,34) — nenhuma parcela difere da outra em mais de
    R$ 0,01. (Arredondar a base para cima e jogar toda a diferença na última gerava parcela
    negativa: 10,00 em 60x → última de -0,03.)
    """
    total = quantize(total)
    total_cents = int(total * 100)
    base_cents, remainder = divmod(abs(total_cents), count)
    sign = -1 if total_cents < 0 else 1
    first_with_extra = count - remainder
    return [
        quantize(Decimal(sign * (base_cents + (1 if i >= first_with_extra else 0))) / 100)
        for i in range(count)
    ]
