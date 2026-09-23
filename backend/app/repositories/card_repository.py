import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.card import CreditCard, CreditCardInstallment, CreditCardInvoice, CreditCardPurchase


def list_cards(db: Session, user_id: uuid.UUID) -> list[CreditCard]:
    stmt = select(CreditCard).where(CreditCard.user_id == user_id).order_by(CreditCard.name)
    return list(db.scalars(stmt))


def get_card(db: Session, user_id: uuid.UUID, card_id: uuid.UUID) -> CreditCard | None:
    stmt = select(CreditCard).where(CreditCard.id == card_id, CreditCard.user_id == user_id)
    return db.scalar(stmt)


def get_invoice_by_competence(
    db: Session, card_id: uuid.UUID, competence: date
) -> CreditCardInvoice | None:
    stmt = select(CreditCardInvoice).where(
        CreditCardInvoice.card_id == card_id, CreditCardInvoice.competence == competence
    )
    return db.scalar(stmt)


def get_invoice_by_id(db: Session, card_id: uuid.UUID, invoice_id: uuid.UUID) -> CreditCardInvoice | None:
    stmt = select(CreditCardInvoice).where(
        CreditCardInvoice.id == invoice_id, CreditCardInvoice.card_id == card_id
    )
    return db.scalar(stmt)


def get_invoice_owned(db: Session, user_id: uuid.UUID, invoice_id: uuid.UUID) -> CreditCardInvoice | None:
    stmt = (
        select(CreditCardInvoice)
        .join(CreditCard, CreditCard.id == CreditCardInvoice.card_id)
        .where(CreditCardInvoice.id == invoice_id, CreditCard.user_id == user_id)
    )
    return db.scalar(stmt)


def list_invoices_owned(
    db: Session, user_id: uuid.UUID, card_id: uuid.UUID | None = None
) -> list[CreditCardInvoice]:
    stmt = (
        select(CreditCardInvoice)
        .join(CreditCard, CreditCard.id == CreditCardInvoice.card_id)
        .where(CreditCard.user_id == user_id)
    )
    if card_id:
        stmt = stmt.where(CreditCardInvoice.card_id == card_id)
    return list(db.scalars(stmt.order_by(CreditCardInvoice.competence.desc())))


def list_invoices(db: Session, card_id: uuid.UUID) -> list[CreditCardInvoice]:
    stmt = (
        select(CreditCardInvoice)
        .where(CreditCardInvoice.card_id == card_id)
        .order_by(CreditCardInvoice.competence.desc())
    )
    return list(db.scalars(stmt))


def list_installments_by_invoice(db: Session, invoice_id: uuid.UUID) -> list[CreditCardInstallment]:
    stmt = (
        select(CreditCardInstallment)
        .where(CreditCardInstallment.invoice_id == invoice_id)
        .order_by(CreditCardInstallment.number)
    )
    return list(db.scalars(stmt))


def list_installments_by_purchase(db: Session, purchase_id: uuid.UUID) -> list[CreditCardInstallment]:
    stmt = (
        select(CreditCardInstallment)
        .where(CreditCardInstallment.purchase_id == purchase_id)
        .order_by(CreditCardInstallment.number)
    )
    return list(db.scalars(stmt))


def get_purchase(db: Session, user_id: uuid.UUID, purchase_id: uuid.UUID) -> CreditCardPurchase | None:
    stmt = select(CreditCardPurchase).where(
        CreditCardPurchase.id == purchase_id, CreditCardPurchase.user_id == user_id
    )
    return db.scalar(stmt)


def list_purchases_by_card(db: Session, card_id: uuid.UUID) -> list[CreditCardPurchase]:
    stmt = (
        select(CreditCardPurchase)
        .where(CreditCardPurchase.card_id == card_id)
        .order_by(CreditCardPurchase.purchase_date.desc())
    )
    return list(db.scalars(stmt))
