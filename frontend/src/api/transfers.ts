import { api } from "@/lib/api"
import type { Transfer } from "@/types"

export interface TransferInput {
  from_account_id: string
  to_account_id: string
  amount: number
  date: string
  description?: string | null
  note?: string | null
}

export const transfersApi = {
  list: () => api.get<Transfer[]>("/transfers").then((r) => r.data),
  create: (payload: TransferInput) => api.post<Transfer>("/transfers", payload).then((r) => r.data),
}
