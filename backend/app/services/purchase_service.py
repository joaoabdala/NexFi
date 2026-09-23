import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.card import CreditCardInstallment, CreditCardPurchase
from app.models.enums import InvoiceStatus, TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.repositories import card_repository, category_repository
from app.schemas.card import CreditCardPurchaseCreate
from app.services.invoice_service import compute_invoice_amount, get_or_create_invoice, reopen_if_paid
from app.utils.dates import add_months, invoice_competence_for_purchase
from app.utils.money import split_installments, to_decimal


def create_purchase(
    db: Session, user_id: uuid.UUID, card_id: uuid.UUID, payload: CreditCardPurchaseCreate
) -> CreditCardPurchase:
    card = card_repository.get_card(db, user_id, card_id)
    if not card:
        raise NotFoundError("Cartão não encontrado.")
    if not card.active:
        raise ValidationError("Não é possível lançar compras em um cartão inativo.")
    if payload.category_id:
        category = category_repository.get_by_id(db, user_id, payload.category_id)
        if not category:
            raise ValidationError("Categoria inválida.")

    amounts = split_installments(payload.total_amount, payload.installments_total)
    first_competence = invoice_competence_for_purchase(payload.purchase_date, card.closing_day)

    try:
        purchase = CreditCardPurchase(
            user_id=user_id,
            card_id=card_id,
            category_id=payload.category_id,
            description=payload.description,
            total_amount=payload.total_amount,
            installments_total=payload.installments_total,
            purchase_date=payload.purchase_date,
        )
        db.add(purchase)
        db.flush()

        touched_invoices = []
        for index, amount in enumerate(amounts, start=1):
            competence = add_months(first_competence, index - 1)
            invoice = get_or_create_invoice(db, card, competence)
            # Fatura já paga (ex.: paga antes do fechamento) volta a ter saldo a pagar, em vez de
            # travar novas compras no período.
            reopen_if_paid(invoice)
            suffix = f" ({index}/{payload.installments_total})" if payload.installments_total > 1 else ""
            description = f"{payload.description}{suffix}"

            txn = Transaction(
                user_id=user_id,
                account_id=None,
                category_id=payload.category_id,
                description=description,
                type=TransactionType.DESPESA,
                amount=amount,
                competence_date=competence,
                payment_date=None,
                status=TransactionStatus.CONFIRMADA,
                origin="CARTAO",
            )
            db.add(txn)
            db.flush()

            installment = CreditCardInstallment(
                purchase_id=purchase.id,
                invoice_id=invoice.id,
                number=index,
                amount=amount,
                transaction_id=txn.id,
            )
            db.add(installment)
            db.flush()

            # Back-reference: permite localizar a parcela/compra a partir da transação
            # (ex.: filtro à vista/parcelado) sem precisar de uma busca reversa.
            txn.card_installment_id = installment.id
            db.add(txn)
            touched_invoices.append(invoice)

        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(purchase)
    return purchase


def purchase_metrics(db: Session, purchase: CreditCardPurchase) -> dict:
    installments = card_repository.list_installments_by_purchase(db, purchase.id)
    invoiced = Decimal("0")
    future = Decimal("0")
    remaining = 0
    for installment in installments:
        invoice = installment.invoice
        if invoice.status == InvoiceStatus.PAGA:
            invoiced += to_decimal(installment.amount)
        else:
            future += to_decimal(installment.amount)
            remaining += 1
    return {
        "invoiced_amount": invoiced,
        "future_amount": future,
        "installments_remaining": remaining,
    }
