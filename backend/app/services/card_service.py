import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.card import CreditCard
from app.models.enums import InvoiceStatus
from app.repositories import account_repository, card_repository, institution_repository
from app.schemas.card import CreditCardCreate, CreditCardUpdate
from app.services.invoice_service import compute_invoice_amount, get_or_create_invoice
from app.utils.dates import invoice_competence_for_purchase
from app.utils.money import to_decimal


def list_cards(db: Session, user_id: uuid.UUID) -> list[dict]:
    cards = card_repository.list_cards(db, user_id)
    return [card_metrics(db, card) for card in cards]


def get_card(db: Session, user_id: uuid.UUID, card_id: uuid.UUID) -> CreditCard:
    card = card_repository.get_card(db, user_id, card_id)
    if not card:
        raise NotFoundError("Cartão não encontrado.")
    return card


def get_cardcard_metrics(db: Session, user_id: uuid.UUID, card_id: uuid.UUID) -> dict:
    return card_metrics(db, get_card(db, user_id, card_id))


def card_metrics(db: Session, card: CreditCard) -> dict:
    current_competence = invoice_competence_for_purchase(date.today(), card.closing_day)
    current_invoice = get_or_create_invoice(db, card, current_competence)
    current_amount = compute_invoice_amount(db, current_invoice)

    outstanding = Decimal("0")
    for invoice in card_repository.list_invoices(db, card.id):
        if invoice.status != InvoiceStatus.PAGA:
            outstanding += compute_invoice_amount(db, invoice)
    db.commit()

    return {
        "id": card.id,
        "institution_id": card.institution_id,
        "name": card.name,
        "brand": card.brand,
        "last_digits": card.last_digits,
        "credit_limit": card.credit_limit,
        "closing_day": card.closing_day,
        "due_day": card.due_day,
        "default_payment_account_id": card.default_payment_account_id,
        "active": card.active,
        "current_invoice_amount": current_amount,
        "available_limit": to_decimal(card.credit_limit) - outstanding,
    }


def create_card(db: Session, user_id: uuid.UUID, payload: CreditCardCreate) -> dict:
    if not institution_repository.get_by_id(db, user_id, payload.institution_id):
        raise ValidationError("Instituição inválida.")
    account = account_repository.get_by_id(db, user_id, payload.default_payment_account_id)
    if not account:
        raise ValidationError("Conta de pagamento padrão inválida.")
    card = CreditCard(user_id=user_id, **payload.model_dump())
    db.add(card)
    db.commit()
    db.refresh(card)
    return card_metrics(db, card)


def update_card(db: Session, user_id: uuid.UUID, card_id: uuid.UUID, payload: CreditCardUpdate) -> dict:
    card = get_card(db, user_id, card_id)
    data = payload.model_dump(exclude_unset=True)
    if data.get("default_payment_account_id"):
        account = account_repository.get_by_id(db, user_id, data["default_payment_account_id"])
        if not account:
            raise ValidationError("Conta de pagamento padrão inválida.")
    for field, value in data.items():
        setattr(card, field, value)
    db.add(card)
    db.commit()
    db.refresh(card)
    return card_metrics(db, card)


def deactivate_card(db: Session, user_id: uuid.UUID, card_id: uuid.UUID) -> None:
    card = get_card(db, user_id, card_id)
    card.active = False
    db.add(card)
    db.commit()
