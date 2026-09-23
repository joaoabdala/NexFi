import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.card import CreditCardInvoiceOut, InvoicePayRequest
from app.services import invoice_service

router = APIRouter()


@router.get("", response_model=list[CreditCardInvoiceOut])
def list_invoices(
    card_id: uuid.UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invoices = invoice_service.list_invoices(db, current_user.id, card_id)
    return [invoice_service.to_invoice_dict(db, invoice) for invoice in invoices]


@router.get("/{invoice_id}", response_model=CreditCardInvoiceOut)
def get_invoice(
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invoice = invoice_service.get_invoice_detail(db, current_user.id, invoice_id)
    return invoice_service.to_invoice_dict(db, invoice)


@router.post("/{invoice_id}/pay", response_model=CreditCardInvoiceOut)
def pay_invoice(
    invoice_id: uuid.UUID,
    payload: InvoicePayRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invoice = invoice_service.pay_invoice(
        db, current_user.id, invoice_id, payload.payment_date, payload.payment_account_id
    )
    return invoice_service.to_invoice_dict(db, invoice)
