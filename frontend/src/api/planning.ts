import { api } from "@/lib/api"
import type { Budget, BudgetSummaryItem, FinancialGoal, RecurrenceRule, TransactionType } from "@/types"

export interface BudgetInput {
  category_id: string
  amount: number
  month?: number | null
  year?: number | null
}

export const budgetsApi = {
  list: () => api.get<Budget[]>("/budgets").then((r) => r.data),
  create: (payload: BudgetInput) => api.post<Budget>("/budgets", payload).then((r) => r.data),
  update: (id: string, amount: number) => api.put<Budget>(`/budgets/${id}`, { amount }).then((r) => r.data),
  remove: (id: string) => api.delete(`/budgets/${id}`),
  summary: (year: number, month: number) =>
    api.get<BudgetSummaryItem[]>("/budgets/summary", { params: { year, month } }).then((r) => r.data),
}

export interface GoalInput {
  name: string
  target_amount: number
  current_amount?: number
  linked_account_id?: string | null
  target_date?: string | null
}

export const goalsApi = {
  list: () => api.get<FinancialGoal[]>("/goals").then((r) => r.data),
  create: (payload: GoalInput) => api.post<FinancialGoal>("/goals", payload).then((r) => r.data),
  update: (id: string, payload: Partial<GoalInput>) =>
    api.put<FinancialGoal>(`/goals/${id}`, payload).then((r) => r.data),
  remove: (id: string) => api.delete(`/goals/${id}`),
}

export interface RecurrenceInput {
  description: string
  type: TransactionType
  amount: number
  account_id: string
  category_id?: string | null
  frequency: "SEMANAL" | "MENSAL" | "ANUAL" | "PERSONALIZADA"
  reference_day?: number | null
  custom_interval_days?: number | null
  start_date: string
  end_date?: string | null
  active?: boolean
}

export interface RecurrenceUpdateInput {
  description?: string
  amount?: number
  category_id?: string | null
  active?: boolean
  end_date?: string | null
}

export const recurrencesApi = {
  list: () => api.get<RecurrenceRule[]>("/recurrences").then((r) => r.data),
  create: (payload: RecurrenceInput) => api.post<RecurrenceRule>("/recurrences", payload).then((r) => r.data),
  update: (id: string, payload: RecurrenceUpdateInput) =>
    api.put<RecurrenceRule>(`/recurrences/${id}`, payload).then((r) => r.data),
  remove: (id: string) => api.delete(`/recurrences/${id}`),
  generate: () => api.post("/recurrences/generate"),
}
