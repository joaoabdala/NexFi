import { api } from "@/lib/api"
import type { Account, AccountType } from "@/types"

export interface AccountInput {
  institution_id: string
  name: string
  type: AccountType
  initial_balance: number
  initial_balance_date: string
  active?: boolean
  include_in_available_worth?: boolean
  include_in_invested_worth?: boolean
  note?: string | null
}

export const accountsApi = {
  list: () => api.get<Account[]>("/accounts").then((r) => r.data),
  create: (payload: AccountInput) => api.post<Account>("/accounts", payload).then((r) => r.data),
  update: (id: string, payload: Partial<AccountInput>) =>
    api.put<Account>(`/accounts/${id}`, payload).then((r) => r.data),
  deactivate: (id: string) => api.delete(`/accounts/${id}`),
  adjustBalance: (id: string, payload: { informed_balance: number; date: string; note?: string | null }) =>
    api.post(`/accounts/${id}/balance-adjustments`, payload).then((r) => r.data),
}
