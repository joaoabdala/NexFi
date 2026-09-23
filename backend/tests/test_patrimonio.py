from datetime import date
from decimal import Decimal

from app.services.dashboard_service import get_summary
from tests.conftest import make_account


def test_gross_and_net_worth_computation(db, user, institution, account, account2):
    """§7: patrimônio bruto = disponível + investido; líquido = bruto - financiamentos."""
    invested = make_account(
        db,
        user,
        institution,
        name="Investimento",
        initial_balance=Decimal("22000.00"),
        include_available=False,
        include_invested=True,
    )

    summary = get_summary(db, user.id)
    # account (1000) + account2 (500) contam como disponível; invested (22000) como investido.
    assert summary["gross_worth"] == Decimal("23500.00")
    # Sem financiamentos cadastrados, líquido == bruto.
    assert summary["net_worth"] == Decimal("23500.00")


def test_net_worth_subtracts_outstanding_financing_balance(db, user, institution, account):
    from app.models.enums import CommitmentType
    from app.schemas.financing import FinancialCommitmentCreate
    from app.services.financing_service import create_commitment

    create_commitment(
        db,
        user.id,
        FinancialCommitmentCreate(
            institution_id=institution.id,
            type=CommitmentType.FINANCIAMENTO,
            name="Financiamento",
            financed_amount=Decimal("400.00"),
            installments_total=4,
            default_installment_amount=Decimal("100.00"),
            start_date=date(2026, 1, 10),
            due_day=10,
        ),
    )

    summary = get_summary(db, user.id)
    assert summary["gross_worth"] == Decimal("1000.00")
    assert summary["net_worth"] == Decimal("600.00")
