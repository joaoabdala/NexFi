import { api } from "@/lib/api"
import type { Page, Transaction, TransactionStatus, TransactionType } from "@/types"

export interface TransactionFilters {
  search?: string
  date_from?: string
  date_to?: string
  type?: TransactionType
  status?: TransactionStatus
  category_id?: string
  account_id?: string
  institution_id?: string
  payment_mode?: "AVISTA" | "PARCELADO"
  min_amount?: number
  max_amount?: number
  sort_by?: string
  sort_dir?: string
  page?: number
  page_size?: number
}

export interface TransactionInput {
  description: string
  type: "RECEITA" | "DESPESA" | "RENDIMENTO"
  amount: number
  account_id: string
  category_id?: string | null
  competence_date: string
  payment_date?: string | null
  status?: TransactionStatus
  note?: string | null
}

export const transactionsApi = {
  list: (filters: TransactionFilters) =>
    api
      .get<Page<Transaction>>("/transactions", { params: filters })
      .then((r) => r.data),
  create: (payload: TransactionInput) =>
    api.post<Transaction>("/transactions", payload).then((r) => r.data),
  update: (id: string, payload: Partial<TransactionInput>) =>
    api.put<Transaction>(`/transactions/${id}`, payload).then((r) => r.data),
  cancel: (id: string) => api.delete(`/transactions/${id}`),
  /** Desfaz transferência, pagamento de fatura ou de parcela (o backend delega ao módulo dono). */
  reverse: (id: string) => api.post(`/transactions/${id}/reverse`),
}
