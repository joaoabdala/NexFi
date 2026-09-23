from datetime import date
from decimal import Decimal

from app.models.enums import AmortizationType, CommitmentInstallmentStatus, CommitmentType
from app.repositories import financing_repository
from app.schemas.financing import AmortizationCreate, FinancialCommitmentCreate
from app.services.financing_service import commitment_with_indicators, create_amortization, create_commitment


def test_amortization_reducao_prazo_eliminates_installments_and_records_discount(
    db, account, institution
):
    commitment = create_commitment(
        db,
        account.user_id,
        FinancialCommitmentCreate(
            institution_id=institution.id,
            type=CommitmentType.FINANCIAMENTO,
            name="Financiamento Amortização",
            financed_amount=Decimal("9000.00"),
            installments_total=9,
            default_installment_amount=Decimal("1000.00"),
            start_date=date(2026, 1, 10),
            due_day=10,
        ),
    )

    # Elimina as parcelas 2 a 9 (nominal R$ 8.000) pagando apenas R$ 6.800 — economia R$ 1.200.
    amortization = create_amortization(
        db,
        account.user_id,
        commitment["id"],
        AmortizationCreate(
            date=date(2026, 2, 1),
            paid_amount=Decimal("6800.00"),
            type=AmortizationType.REDUCAO_PRAZO,
            account_id=account.id,
            installment_numbers=list(range(2, 10)),
        ),
    )

    assert amortization.nominal_amortized_amount == Decimal("8000.00")
    assert amortization.discount_obtained == Decimal("1200.00")

    installments = financing_repository.list_installments(db, commitment["id"])
    affected = [i for i in installments if i.number >= 2]
    assert all(i.status == CommitmentInstallmentStatus.AMORTIZADA for i in affected)
    assert all(i.amortization_id == amortization.id for i in affected)

    # Rastreabilidade completa: a associação N:N registra exatamente quais parcelas foram afetadas.
    assert sorted(link.commitment_installment.number for link in amortization.affected_installments) == list(
        range(2, 10)
    )

    updated = commitment_with_indicators(db, financing_repository.get_commitment(db, account.user_id, commitment["id"]))
    assert updated["installments_amortized"] == 8
    assert updated["accumulated_savings"] == Decimal("1200.00")
    assert updated["outstanding_balance"] == Decimal("1000.00")  # só a parcela 1 permanece pendente


def test_amortization_cannot_target_already_paid_installment(db, account, institution):
    from datetime import date as _date

    import pytest

    from app.core.exceptions import ValidationError
    from app.schemas.financing import InstallmentPayRequest
    from app.services.financing_service import pay_installment

    commitment = create_commitment(
        db,
        account.user_id,
        FinancialCommitmentCreate(
            institution_id=institution.id,
            type=CommitmentType.FINANCIAMENTO,
            name="Financiamento Amortização 2",
            financed_amount=Decimal("3000.00"),
            installments_total=3,
            default_installment_amount=Decimal("1000.00"),
            start_date=_date(2026, 1, 10),
            due_day=10,
        ),
    )
    first_installment = financing_repository.list_installments(db, commitment["id"])[0]
    pay_installment(
        db,
        account.user_id,
        commitment["id"],
        first_installment.id,
        InstallmentPayRequest(payment_date=_date(2026, 1, 10), account_id=account.id),
    )

    with pytest.raises(ValidationError):
        create_amortization(
            db,
            account.user_id,
            commitment["id"],
            AmortizationCreate(
                date=_date(2026, 2, 1),
                paid_amount=Decimal("500.00"),
                type=AmortizationType.REDUCAO_PRAZO,
                account_id=account.id,
                installment_numbers=[1],
            ),
        )
