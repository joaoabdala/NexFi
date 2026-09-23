import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.card import CreditCard, CreditCardInvoice
from app.models.enums import InvoiceStatus, TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.repositories import card_repository
from app.utils.dates import safe_day_in_month, local_today
from app.utils.money import quantize, to_decimal


def invoice_dates_for_competence(card: CreditCard, competence: date) -> tuple[date, date]:
    closing_date = safe_day_in_month(competence.year, competence.month, card.closing_day)
    if card.due_day >= card.closing_day:
        due_date = safe_day_in_month(competence.year, competence.month, card.due_day)
    else:
        next_month = competence.month % 12 + 1
        next_year = competence.year + (1 if competence.month == 12 else 0)
        due_date = safe_day_in_month(next_year, next_month, card.due_day)
    return closing_date, due_date


def get_or_create_invoice(db: Session, card: CreditCard, competence: date) -> CreditCardInvoice:
    invoice = card_repository.get_invoice_by_competence(db, card.id, competence)
    if invoice:
        return invoice
    closing_date, due_date = invoice_dates_for_competence(card, competence)
    invoice = CreditCardInvoice(
        card_id=card.id,
        competence=competence,
        closing_date=closing_date,
        due_date=due_date,
        status=InvoiceStatus.ABERTA,
    )
    db.add(invoice)
    db.flush()
    return invoice


def compute_invoice_amount(db: Session, invoice: CreditCardInvoice) -> Decimal:
    installments = card_repository.list_installments_by_invoice(db, invoice.id)
    return quantize(sum((to_decimal(i.amount) for i in installments), Decimal("0")))


def compute_invoice_paid(db: Session, invoice: CreditCardInvoice) -> Decimal:
    """Soma dos pagamentos confirmados da fatura. Uma fatura pode ter mais de um pagamento:
    quando uma compra entra numa fatura já paga (paga antes do fechamento, por exemplo), ela
    reabre e o próximo pagamento cobre só a diferença."""
    stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.invoice_id == invoice.id,
        Transaction.type == TransactionType.PAGAMENTO_FATURA,
        Transaction.status == TransactionStatus.CONFIRMADA,
    )
    return quantize(to_decimal(db.scalar(stmt)))


def reopen_if_paid(invoice: CreditCardInvoice) -> None:
    """Chamada quando entra uma compra nova: a fatura volta a ter saldo a pagar."""
    if invoice.status == InvoiceStatus.PAGA:
        invoice.status = InvoiceStatus.ABERTA
        refresh_invoice_status(invoice)


def refresh_invoice_status(invoice: CreditCardInvoice) -> CreditCardInvoice:
    if invoice.status == InvoiceStatus.PAGA:
        return invoice
    today = local_today()
    if today > invoice.due_date:
        invoice.status = InvoiceStatus.VENCIDA
    elif today >= invoice.closing_date:
        invoice.status = InvoiceStatus.FECHADA
    else:
        invoice.status = InvoiceStatus.ABERTA
    return invoice


def to_invoice_dict(db: Session, invoice: CreditCardInvoice) -> dict:
    installments = card_repository.list_installments_by_invoice(db, invoice.id)
    installment_dicts = [
        {
            "id": i.id,
            "purchase_id": i.purchase_id,
            "invoice_id": i.invoice_id,
            "number": i.number,
            "amount": i.amount,
            "description": i.purchase.description if i.purchase else None,
            "installments_total": i.purchase.installments_total if i.purchase else None,
        }
        for i in installments
    ]
    return {
        "id": invoice.id,
        "card_id": invoice.card_id,
        "competence": invoice.competence,
        "closing_date": invoice.closing_date,
        "due_date": invoice.due_date,
        "status": invoice.status,
        "amount": compute_invoice_amount(db, invoice),
        "paid_amount": compute_invoice_paid(db, invoice),
        "payment_date": invoice.payment_date,
        "payment_account_id": invoice.payment_account_id,
        "installments": installment_dicts,
    }


def list_invoices(
    db: Session, user_id: uuid.UUID, card_id: uuid.UUID | None = None
) -> list[CreditCardInvoice]:
    invoices = card_repository.list_invoices_owned(db, user_id, card_id)
    for invoice in invoices:
        refresh_invoice_status(invoice)
    db.commit()
    return invoices


def get_invoice_detail(db: Session, user_id: uuid.UUID, invoice_id: uuid.UUID) -> CreditCardInvoice:
    invoice = card_repository.get_invoice_owned(db, user_id, invoice_id)
    if not invoice:
        raise NotFoundError("Fatura não encontrada.")
    refresh_invoice_status(invoice)
    db.commit()
    return invoice


def pay_invoice(
    db: Session,
    user_id: uuid.UUID,
    invoice_id: uuid.UUID,
    payment_date: date,
    payment_account_id: uuid.UUID | None,
) -> CreditCardInvoice:
    invoice = card_repository.get_invoice_owned(db, user_id, invoice_id)
    if not invoice:
        raise NotFoundError("Fatura não encontrada.")
    # Trava a linha da fatura (Postgres) até o commit: um clique duplo não gera dois pagamentos.
    db.refresh(invoice, with_for_update=True)
    if invoice.status == InvoiceStatus.PAGA:
        raise ValidationError("Esta fatura já foi paga.")
    card = invoice.card

    account_id = payment_account_id or card.default_payment_account_id
    if payment_account_id:
        from app.repositories import account_repository

        account = account_repository.get_by_id(db, user_id, payment_account_id)
        if not account:
            raise ValidationError("Conta de pagamento inválida.")

    amount = quantize(compute_invoice_amount(db, invoice) - compute_invoice_paid(db, invoice))
    if amount <= 0:
        raise ValidationError("Fatura sem valor a pagar.")

    try:
        # Regra crítica: o pagamento da fatura NUNCA gera uma nova DESPESA — as despesas já
        # foram registradas em cada CreditCardInstallment.transaction. Este lançamento é do
        # tipo PAGAMENTO_FATURA, que apenas debita a conta e é excluído do somatório de
        # despesas do período (ver dashboard_service).
        payment_txn = Transaction(
            user_id=user_id,
            account_id=account_id,
            category_id=None,
            description=f"Pagamento fatura {card.name} — {invoice.competence.strftime('%m/%Y')}",
            type=TransactionType.PAGAMENTO_FATURA,
            amount=amount,
            competence_date=invoice.competence,
            payment_date=payment_date,
            status=TransactionStatus.CONFIRMADA,
            origin="PAGAMENTO_FATURA",
            invoice_id=invoice.id,
        )
        db.add(payment_txn)
        db.flush()

        invoice.status = InvoiceStatus.PAGA
        invoice.payment_date = payment_date
        invoice.payment_account_id = account_id
        invoice.payment_transaction_id = payment_txn.id
        db.add(invoice)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(invoice)
    return invoice


def undo_invoice_payment(
    db: Session,
    user_id: uuid.UUID,
    invoice_id: uuid.UUID,
    transaction_id: uuid.UUID | None = None,
) -> CreditCardInvoice:
    """Desfaz um pagamento de fatura (o mais recente, ou o informado).

    O lançamento de pagamento fica CANCELADO (histórico preservado) e o valor volta para a conta;
    a fatura volta a ter saldo a pagar. Se ainda restarem outros pagamentos que cubram o total,
    ela continua PAGA.
    """
    invoice = card_repository.get_invoice_owned(db, user_id, invoice_id)
    if not invoice:
        raise NotFoundError("Fatura não encontrada.")
    db.refresh(invoice, with_for_update=True)

    stmt = (
        select(Transaction)
        .where(
            Transaction.invoice_id == invoice.id,
            Transaction.type == TransactionType.PAGAMENTO_FATURA,
            Transaction.status == TransactionStatus.CONFIRMADA,
        )
        .order_by(Transaction.payment_date.desc(), Transaction.created_at.desc())
    )
    payments = list(db.scalars(stmt))
    if transaction_id is not None:
        payments_to_undo = [p for p in payments if p.id == transaction_id]
    else:
        payments_to_undo = payments[:1]
    if not payments_to_undo:
        raise ValidationError("Não há pagamento ativo para desfazer nesta fatura.")

    try:
        payments_to_undo[0].status = TransactionStatus.CANCELADA
        db.add(payments_to_undo[0])
        db.flush()

        remaining = [p for p in payments if p.id != payments_to_undo[0].id]
        latest = remaining[0] if remaining else None
        invoice.payment_date = latest.payment_date if latest else None
        invoice.payment_account_id = latest.account_id if latest else None
        invoice.payment_transaction_id = latest.id if latest else None

        amount = compute_invoice_amount(db, invoice)
        if latest and compute_invoice_paid(db, invoice) >= amount > 0:
            invoice.status = InvoiceStatus.PAGA
        else:
            invoice.status = InvoiceStatus.ABERTA
            refresh_invoice_status(invoice)
        db.add(invoice)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(invoice)
    return invoice
