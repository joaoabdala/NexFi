import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.enums import (
    AmortizationType,
    CommitmentInstallmentStatus,
    CommitmentStatus,
    TransactionStatus,
    TransactionType,
)
from app.models.financing import (
    Amortization,
    AmortizationInstallment,
    CommitmentInstallment,
    FinancialCommitment,
)
from app.models.transaction import Transaction
from app.repositories import account_repository, financing_repository, institution_repository
from app.schemas.financing import (
    AmortizationCreate,
    FinancialCommitmentCreate,
    FinancialCommitmentUpdate,
    InstallmentPayRequest,
)
from app.utils.dates import add_months
from app.utils.money import quantize, to_decimal


def _recompute_outstanding_balance(db: Session, commitment: FinancialCommitment) -> None:
    """Recalcula o saldo devedor como a soma de ``updated_amount`` das parcelas PENDENTES.

    Evita divergência de aritmética incremental: parcelas PAGA ou AMORTIZADA saem da soma
    automaticamente, e reduções de valor (REDUCAO_PARCELA) refletem-se direto no total.
    """
    installments = financing_repository.list_installments(db, commitment.id)
    total = quantize(
        sum(
            (
                to_decimal(i.updated_amount)
                for i in installments
                if i.status == CommitmentInstallmentStatus.PENDENTE
            ),
            Decimal("0"),
        )
    )
    commitment.outstanding_balance = total
    if total <= 0 and all(i.status != CommitmentInstallmentStatus.PENDENTE for i in installments):
        commitment.status = CommitmentStatus.QUITADO
    db.add(commitment)


def _ensure_active(commitment: FinancialCommitment) -> None:
    if commitment.status != CommitmentStatus.ATIVO:
        raise ValidationError("Só é possível pagar ou amortizar financiamentos ativos.")


def _generate_schedule(db: Session, commitment: FinancialCommitment) -> None:
    for number in range(1, commitment.installments_total + 1):
        due_date = add_months(commitment.start_date, number - 1)
        installment = CommitmentInstallment(
            commitment_id=commitment.id,
            number=number,
            due_date=due_date,
            original_amount=commitment.default_installment_amount,
            updated_amount=commitment.default_installment_amount,
            status=CommitmentInstallmentStatus.PENDENTE,
        )
        db.add(installment)


def list_commitments(db: Session, user_id: uuid.UUID) -> list[dict]:
    return [
        commitment_with_indicators(db, c) for c in financing_repository.list_commitments(db, user_id)
    ]


def get_commitment(db: Session, user_id: uuid.UUID, commitment_id: uuid.UUID) -> FinancialCommitment:
    commitment = financing_repository.get_commitment(db, user_id, commitment_id)
    if not commitment:
        raise NotFoundError("Financiamento não encontrado.")
    return commitment


def get_commitment_with_indicators(db: Session, user_id: uuid.UUID, commitment_id: uuid.UUID) -> dict:
    return commitment_with_indicators(db, get_commitment(db, user_id, commitment_id))


def commitment_with_indicators(db: Session, commitment: FinancialCommitment) -> dict:
    installments = financing_repository.list_installments(db, commitment.id)
    paid = [i for i in installments if i.status == CommitmentInstallmentStatus.PAGA]
    pending = [i for i in installments if i.status == CommitmentInstallmentStatus.PENDENTE]
    amortized = [i for i in installments if i.status == CommitmentInstallmentStatus.AMORTIZADA]
    total_paid = quantize(sum((to_decimal(i.paid_amount or 0) for i in paid), Decimal("0")))

    amortizations = financing_repository.list_amortizations(db, commitment.id)
    total_amortized = quantize(
        sum((to_decimal(a.nominal_amortized_amount) for a in amortizations), Decimal("0"))
    )
    early_payment_discounts = sum(
        (
            to_decimal(i.updated_amount) - to_decimal(i.paid_amount)
            for i in paid
            if i.paid_amount is not None and to_decimal(i.paid_amount) < to_decimal(i.updated_amount)
        ),
        Decimal("0"),
    )
    # Economia = descontos das amortizações + descontos de parcelas pagas antes do vencimento
    # por um valor menor que o da parcela.
    accumulated_savings = quantize(
        sum((to_decimal(a.discount_obtained) for a in amortizations), Decimal("0"))
        + early_payment_discounts
    )

    next_installment = pending[0] if pending else None

    return {
        "id": commitment.id,
        "institution_id": commitment.institution_id,
        "type": commitment.type,
        "name": commitment.name,
        "asset_value": commitment.asset_value,
        "down_payment": commitment.down_payment,
        "financed_amount": commitment.financed_amount,
        "interest_rate": commitment.interest_rate,
        "installments_total": commitment.installments_total,
        "default_installment_amount": commitment.default_installment_amount,
        "start_date": commitment.start_date,
        "due_day": commitment.due_day,
        "outstanding_balance": commitment.outstanding_balance,
        "status": commitment.status,
        "note": commitment.note,
        "installments_paid": len(paid),
        "installments_remaining": len(pending),
        "installments_amortized": len(amortized),
        "total_paid": total_paid,
        "total_amortized": total_amortized,
        "accumulated_savings": accumulated_savings,
        "next_installment": next_installment,
    }


def create_commitment(
    db: Session, user_id: uuid.UUID, payload: FinancialCommitmentCreate
) -> dict:
    if not institution_repository.get_by_id(db, user_id, payload.institution_id):
        raise ValidationError("Instituição inválida.")

    try:
        commitment = FinancialCommitment(
            user_id=user_id,
            outstanding_balance=Decimal("0"),
            status=CommitmentStatus.ATIVO,
            **payload.model_dump(),
        )
        db.add(commitment)
        db.flush()
        _generate_schedule(db, commitment)
        db.flush()
        # Saldo devedor = soma das parcelas pendentes, a mesma regra usada depois de cada
        # pagamento. Usar financed_amount aqui fazia a dívida "pular" no 1º pagamento
        # (ex.: 100 mil na criação → 359 mil após pagar 1 de 360 parcelas de 1 mil).
        _recompute_outstanding_balance(db, commitment)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(commitment)
    return commitment_with_indicators(db, commitment)


def update_commitment(
    db: Session, user_id: uuid.UUID, commitment_id: uuid.UUID, payload: FinancialCommitmentUpdate
) -> dict:
    commitment = get_commitment(db, user_id, commitment_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(commitment, field, value)
    db.add(commitment)
    db.commit()
    db.refresh(commitment)
    return commitment_with_indicators(db, commitment)


def pay_installment(
    db: Session,
    user_id: uuid.UUID,
    commitment_id: uuid.UUID,
    installment_id: uuid.UUID,
    payload: InstallmentPayRequest,
) -> CommitmentInstallment:
    commitment = get_commitment(db, user_id, commitment_id)
    _ensure_active(commitment)
    installment = financing_repository.get_installment(db, commitment.id, installment_id)
    if not installment:
        raise NotFoundError("Parcela não encontrada.")
    db.refresh(installment, with_for_update=True)  # clique duplo não paga duas vezes
    if installment.status != CommitmentInstallmentStatus.PENDENTE:
        raise ValidationError("Apenas parcelas pendentes podem ser pagas.")
    account = account_repository.get_by_id(db, user_id, payload.account_id)
    if not account:
        raise ValidationError("Conta inválida.")

    amount = quantize(payload.paid_amount if payload.paid_amount is not None else installment.updated_amount)

    try:
        txn = Transaction(
            user_id=user_id,
            account_id=account.id,
            category_id=None,
            description=f"Parcela {installment.number}/{commitment.installments_total} — {commitment.name}",
            type=TransactionType.PAGAMENTO_FINANCIAMENTO,
            amount=amount,
            competence_date=installment.due_date,
            payment_date=payload.payment_date,
            status=TransactionStatus.CONFIRMADA,
            origin="FINANCIAMENTO",
            commitment_installment_id=installment.id,
        )
        db.add(txn)
        db.flush()

        installment.status = CommitmentInstallmentStatus.PAGA
        installment.paid_amount = amount
        installment.payment_date = payload.payment_date
        installment.transaction_id = txn.id
        db.add(installment)
        db.flush()

        _recompute_outstanding_balance(db, commitment)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(installment)
    return installment


def create_amortization(
    db: Session, user_id: uuid.UUID, commitment_id: uuid.UUID, payload: AmortizationCreate
) -> Amortization:
    commitment = get_commitment(db, user_id, commitment_id)
    _ensure_active(commitment)
    if payload.type == AmortizationType.REDUCAO_PARCELA:
        # Desativada: a fórmula abatia o *desconto* das parcelas em vez do valor pago (pagar
        # 2 mil de um saldo de 10 mil deixava a dívida em 2 mil). Reativar exige que o usuário
        # informe o novo valor da parcela calculado pelo banco.
        raise ValidationError(
            "Amortização com redução do valor das parcelas não está disponível. "
            "Use a redução de prazo (escolha as parcelas quitadas)."
        )
    account = account_repository.get_by_id(db, user_id, payload.account_id)
    if not account:
        raise ValidationError("Conta inválida.")

    all_installments = financing_repository.list_installments(db, commitment.id)
    pending_by_number = {
        i.number: i for i in all_installments if i.status == CommitmentInstallmentStatus.PENDENTE
    }
    if not pending_by_number:
        raise ValidationError("Não há parcelas pendentes para amortizar.")

    if payload.installment_numbers:
        if len(set(payload.installment_numbers)) != len(payload.installment_numbers):
            raise ValidationError("A mesma parcela foi informada mais de uma vez.")
        numbers = payload.installment_numbers
    elif payload.type == AmortizationType.REDUCAO_PARCELA:
        numbers = list(pending_by_number.keys())
    else:
        raise ValidationError(
            "Informe as parcelas afetadas (installment_numbers) para amortização REDUCAO_PRAZO."
        )

    target_installments = []
    for n in numbers:
        installment = pending_by_number.get(n)
        if installment is None:
            raise ValidationError(
                f"Parcela {n} não existe ou já não está pendente (paga/amortizada/inexistente)."
            )
        target_installments.append(installment)

    nominal_amortized = quantize(
        sum((to_decimal(i.updated_amount) for i in target_installments), Decimal("0"))
    )
    paid_amount = quantize(payload.paid_amount)
    if paid_amount > nominal_amortized:
        raise ValidationError(
            "O valor pago é maior que a soma das parcelas selecionadas "
            f"(R$ {nominal_amortized}). Selecione mais parcelas ou revise o valor."
        )
    discount = quantize(nominal_amortized - paid_amount)

    try:
        txn = Transaction(
            user_id=user_id,
            account_id=account.id,
            category_id=None,
            description=f"Amortização — {commitment.name}",
            type=TransactionType.AMORTIZACAO,
            amount=paid_amount,
            competence_date=payload.date,
            payment_date=payload.date,
            status=TransactionStatus.CONFIRMADA,
            origin="AMORTIZACAO",
        )
        db.add(txn)
        db.flush()

        amortization = Amortization(
            user_id=user_id,
            commitment_id=commitment.id,
            date=payload.date,
            paid_amount=paid_amount,
            nominal_amortized_amount=nominal_amortized,
            discount_obtained=discount,
            type=payload.type,
            account_id=account.id,
            note=payload.note,
            transaction_id=txn.id,
        )
        db.add(amortization)
        db.flush()

        for installment in target_installments:
            db.add(
                AmortizationInstallment(
                    amortization_id=amortization.id, commitment_installment_id=installment.id
                )
            )
            if payload.type == AmortizationType.REDUCAO_PRAZO:
                installment.status = CommitmentInstallmentStatus.AMORTIZADA
                installment.amortization_id = amortization.id
            else:
                # REDUCAO_PARCELA: reduz proporcionalmente o valor das parcelas restantes,
                # que continuam PENDENTES (ainda serão pagas, porém com valor menor).
                share = to_decimal(installment.updated_amount) / nominal_amortized if nominal_amortized else 0
                reduction = quantize(discount * share)
                installment.updated_amount = quantize(to_decimal(installment.updated_amount) - reduction)
                installment.amortization_id = amortization.id
            db.add(installment)
        db.flush()

        _recompute_outstanding_balance(db, commitment)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(amortization)
    return amortization
