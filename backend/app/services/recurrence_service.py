import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.enums import RecurrenceFrequency, TransactionStatus
from app.models.recurrence import RecurrenceRule
from app.models.transaction import Transaction
from app.repositories import account_repository, category_repository, recurrence_repository
from app.schemas.recurrence import RecurrenceCreate, RecurrenceUpdate
from app.utils.dates import add_months, safe_day_in_month, local_today


# Teto de lançamentos gerados por regra em uma chamada: uma única requisição não pode encher o
# banco (Neon Free bloqueia escritas acima de 0,5 GB). O restante é gerado nas próximas chamadas.
MAX_GENERATED_PER_RULE = 400


def _next_occurrence(rule: RecurrenceRule, current: date) -> date:
    if rule.frequency == RecurrenceFrequency.SEMANAL:
        return current + timedelta(days=7)
    # Sem dia de referência, usa o dia da data de início: uma regra iniciada em 31/01 não pode
    # "escorregar" para o dia 28 em todos os meses depois de passar por fevereiro.
    reference_day = rule.reference_day or rule.start_date.day
    if rule.frequency == RecurrenceFrequency.MENSAL:
        nxt = add_months(current, 1)
        return safe_day_in_month(nxt.year, nxt.month, reference_day)
    if rule.frequency == RecurrenceFrequency.ANUAL:
        nxt = add_months(current, 12)
        return safe_day_in_month(nxt.year, nxt.month, reference_day)
    # PERSONALIZADA
    return current + timedelta(days=rule.custom_interval_days or 30)


def list_recurrences(db: Session, user_id: uuid.UUID) -> list[RecurrenceRule]:
    return recurrence_repository.list_by_user(db, user_id)


def get_recurrence(db: Session, user_id: uuid.UUID, rule_id: uuid.UUID) -> RecurrenceRule:
    rule = recurrence_repository.get_by_id(db, user_id, rule_id)
    if not rule:
        raise NotFoundError("Recorrência não encontrada.")
    return rule


def create_recurrence(db: Session, user_id: uuid.UUID, payload: RecurrenceCreate) -> RecurrenceRule:
    if not account_repository.get_by_id(db, user_id, payload.account_id):
        raise ValidationError("Conta inválida.")
    if payload.category_id and not category_repository.get_by_id(db, user_id, payload.category_id):
        raise ValidationError("Categoria inválida.")
    rule = RecurrenceRule(user_id=user_id, **payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    generate_pending_transactions(db, user_id, rule_id=rule.id)
    db.refresh(rule)
    return rule


def update_recurrence(
    db: Session, user_id: uuid.UUID, rule_id: uuid.UUID, payload: RecurrenceUpdate
) -> RecurrenceRule:
    rule = get_recurrence(db, user_id, rule_id)
    data = payload.model_dump(exclude_unset=True)
    # A criação já valida a categoria; a edição também precisa — senão dava para apontar a regra
    # para a categoria de outro usuário (e ver o nome dela no dashboard).
    if data.get("category_id") and not category_repository.get_by_id(db, user_id, data["category_id"]):
        raise ValidationError("Categoria inválida.")
    for field, value in data.items():
        setattr(rule, field, value)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def delete_recurrence(db: Session, user_id: uuid.UUID, rule_id: uuid.UUID) -> None:
    rule = get_recurrence(db, user_id, rule_id)
    rule.active = False
    db.add(rule)
    # Lançamentos futuros ainda pendentes dessa regra deixam de fazer sentido: sem isso eles
    # continuavam na projeção de saldo depois de a recorrência ser excluída.
    future_pending = db.scalars(
        select(Transaction).where(
            Transaction.recurrence_rule_id == rule.id,
            Transaction.user_id == user_id,
            Transaction.status == TransactionStatus.PENDENTE,
            Transaction.competence_date >= local_today(),
        )
    )
    for txn in future_pending:
        txn.status = TransactionStatus.CANCELADA
        db.add(txn)
    db.commit()


def generate_pending_transactions(
    db: Session, user_id: uuid.UUID, rule_id: uuid.UUID | None = None
) -> int:
    """Gera transações PENDENTE futuras dentro do horizonte configurado.

    Idempotente: cada regra avança ``last_generated_competence``, garantindo que uma
    mesma competência nunca seja gerada duas vezes para a mesma regra.
    """
    rules = (
        [get_recurrence(db, user_id, rule_id)]
        if rule_id
        else recurrence_repository.list_active(db, user_id)
    )
    horizon = local_today() + timedelta(days=30 * settings.RECURRENCE_HORIZON_MONTHS)
    created = 0

    for rule in rules:
        if not rule.active:
            continue
        cursor = rule.last_generated_competence or rule.start_date
        first_iteration = rule.last_generated_competence is None
        generated_for_rule = 0
        while cursor <= horizon and generated_for_rule < MAX_GENERATED_PER_RULE:
            if rule.end_date and cursor > rule.end_date:
                break
            if cursor >= rule.start_date and (first_iteration or cursor > rule.last_generated_competence):
                txn = Transaction(
                    user_id=user_id,
                    account_id=rule.account_id,
                    category_id=rule.category_id,
                    description=rule.description,
                    type=rule.type,
                    amount=rule.amount,
                    competence_date=cursor,
                    payment_date=None,
                    status=TransactionStatus.PENDENTE,
                    origin="RECORRENCIA",
                    recurrence_rule_id=rule.id,
                )
                db.add(txn)
                rule.last_generated_competence = cursor
                created += 1
                generated_for_rule += 1
            first_iteration = False
            cursor = _next_occurrence(rule, cursor)
        db.add(rule)

    db.commit()
    return created
