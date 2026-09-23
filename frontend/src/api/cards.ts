import { api } from "@/lib/api"
import type { CreditCard, CreditCardInvoice, CreditCardPurchase } from "@/types"

export interface CardInput {
  institution_id: string
  name: string
  brand?: string | null
  last_digits?: string | null
  credit_limit: number
  closing_day: number
  due_day: number
  default_payment_account_id: string
  active?: boolean
}

export interface PurchaseInput {
  description: string
  total_amount: number
  installments_total: number
  purchase_date: string
  category_id?: string | null
}

export const cardsApi = {
  list: () => api.get<CreditCard[]>("/cards").then((r) => r.data),
  create: (payload: CardInput) => api.post<CreditCard>("/cards", payload).then((r) => r.data),
  update: (id: string, payload: Partial<CardInput>) =>
    api.put<CreditCard>(`/cards/${id}`, payload).then((r) => r.data),
  deactivate: (id: string) => api.delete(`/cards/${id}`),
  createPurchase: (cardId: string, payload: PurchaseInput) =>
    api.post<CreditCardPurchase>(`/cards/${cardId}/purchases`, payload).then((r) => r.data),
  listPurchases: (cardId: string) =>
    api.get<CreditCardPurchase[]>(`/cards/${cardId}/purchases`).then((r) => r.data),
}

export const invoicesApi = {
  list: (cardId?: string) =>
    api.get<CreditCardInvoice[]>("/invoices", { params: cardId ? { card_id: cardId } : {} }).then((r) => r.data),
  get: (id: string) => api.get<CreditCardInvoice>(`/invoices/${id}`).then((r) => r.data),
  pay: (id: string, payload: { payment_date: string; payment_account_id?: string | null }) =>
    api.post<CreditCardInvoice>(`/invoices/${id}/pay`, payload).then((r) => r.data),
}
