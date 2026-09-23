export type UUID = string

export type UserRole = "ADMIN" | "USER"

export interface User {
  id: UUID
  email: string
  name: string
  timezone: string
  locale: string
  role: UserRole
}

export interface AdminUser {
  id: UUID
  email: string
  name: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export type AccountType =
  | "CONTA_CORRENTE"
  | "CONTA_DIGITAL"
  | "POUPANCA"
  | "DINHEIRO"
  | "COFRINHO_RESERVA"
  | "INVESTIMENTO"
  | "OUTROS"

export type CategoryKind = "RECEITA" | "DESPESA" | "AMBOS"

export type TransactionType =
  | "RECEITA"
  | "DESPESA"
  | "TRANSFERENCIA"
  | "RENDIMENTO"
  | "AJUSTE"
  | "PAGAMENTO_FATURA"
  | "PAGAMENTO_FINANCIAMENTO"
  | "AMORTIZACAO"

export type TransactionStatus = "PENDENTE" | "CONFIRMADA" | "CANCELADA"

export type InvoiceStatus = "ABERTA" | "FECHADA" | "PAGA" | "VENCIDA"

export type CommitmentType = "FINANCIAMENTO" | "EMPRESTIMO" | "CONSORCIO" | "OUTROS"
export type CommitmentStatus = "ATIVO" | "QUITADO" | "CANCELADO"
export type CommitmentInstallmentStatus = "PENDENTE" | "PAGA" | "AMORTIZADA" | "CANCELADA"
export type AmortizationType = "REDUCAO_PRAZO" | "REDUCAO_PARCELA"
export type RecurrenceFrequency = "SEMANAL" | "MENSAL" | "ANUAL" | "PERSONALIZADA"
export type GoalStatus = "EM_ANDAMENTO" | "CONCLUIDA" | "CANCELADA"

export interface Institution {
  id: UUID
  name: string
  short_name: string | null
  active: boolean
  note: string | null
}

export interface Account {
  id: UUID
  institution_id: UUID
  institution_name: string | null
  name: string
  type: AccountType
  initial_balance: string
  initial_balance_date: string
  active: boolean
  include_in_available_worth: boolean
  include_in_invested_worth: boolean
  note: string | null
  current_balance: string
}

export interface Category {
  id: UUID
  name: string
  kind: CategoryKind
  parent_id: UUID | null
  active: boolean
  children: Category[]
}

export interface Transaction {
  id: UUID
  description: string
  type: TransactionType
  amount: string
  account_id: UUID | null
  category_id: UUID | null
  competence_date: string
  payment_date: string | null
  status: TransactionStatus
  note: string | null
  origin: string
  transfer_id: UUID | null
  invoice_id: UUID | null
  commitment_installment_id: UUID | null
  amortization_id: UUID | null
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface Transfer {
  id: UUID
  from_account_id: UUID
  to_account_id: UUID
  amount: string
  date: string
  description: string | null
  note: string | null
}

export interface CreditCard {
  id: UUID
  institution_id: UUID
  name: string
  brand: string | null
  last_digits: string | null
  credit_limit: string
  closing_day: number
  due_day: number
  default_payment_account_id: UUID
  active: boolean
  current_invoice_amount: string
  available_limit: string
}

export interface CreditCardInstallment {
  id: UUID
  purchase_id: UUID
  invoice_id: UUID
  number: number
  amount: string
  description: string | null
  installments_total: number | null
}

export interface CreditCardInvoice {
  id: UUID
  card_id: UUID
  competence: string
  closing_date: string
  due_date: string
  status: InvoiceStatus
  amount: string
  /** Soma dos pagamentos já feitos (uma fatura reaberta por compra nova pode ter mais de um). */
  paid_amount: string
  payment_date: string | null
  payment_account_id: UUID | null
  installments: CreditCardInstallment[]
}

export interface CreditCardPurchase {
  id: UUID
  card_id: UUID
  description: string
  total_amount: string
  installments_total: number
  purchase_date: string
  category_id: UUID | null
  invoiced_amount: string
  future_amount: string
  installments_remaining: number
}

export interface CommitmentInstallment {
  id: UUID
  commitment_id: UUID
  number: number
  due_date: string
  original_amount: string
  updated_amount: string
  paid_amount: string | null
  payment_date: string | null
  status: CommitmentInstallmentStatus
  amortization_id: UUID | null
}

export interface FinancialCommitment {
  id: UUID
  institution_id: UUID
  type: CommitmentType
  name: string
  asset_value: string | null
  down_payment: string | null
  financed_amount: string
  interest_rate: string | null
  installments_total: number
  default_installment_amount: string
  start_date: string
  due_day: number
  outstanding_balance: string
  status: CommitmentStatus
  note: string | null
  installments_paid: number
  installments_remaining: number
  installments_amortized: number
  total_paid: string
  total_amortized: string
  accumulated_savings: string
  next_installment: CommitmentInstallment | null
}

export interface Amortization {
  id: UUID
  commitment_id: UUID
  date: string
  paid_amount: string
  nominal_amortized_amount: string
  discount_obtained: string
  type: AmortizationType
  account_id: UUID
  note: string | null
  affected_installment_numbers: number[]
}

export interface Budget {
  id: UUID
  category_id: UUID
  amount: string
  month: number | null
  year: number | null
  is_default: boolean
}

export interface BudgetSummaryItem {
  category_id: UUID
  category_name: string
  budget_amount: string
  realized_amount: string
  remaining_amount: string
  percentage_used: string
}

export interface FinancialGoal {
  id: UUID
  name: string
  target_amount: string
  current_amount: string
  linked_account_id: UUID | null
  target_date: string | null
  status: GoalStatus
  progress_percentage: string
}

export interface RecurrenceRule {
  id: UUID
  description: string
  type: TransactionType
  amount: string
  account_id: UUID
  category_id: UUID | null
  frequency: RecurrenceFrequency
  reference_day: number | null
  start_date: string
  end_date: string | null
  active: boolean
  last_generated_competence: string | null
}

export interface DashboardSummary {
  available_balance: string
  income_month: string
  expenses_month: string
  result_month: string
  gross_worth: string
  net_worth: string
  yield_month: string
}

export interface AccountSummary {
  id: UUID
  institution_name: string
  name: string
  type: string
  balance: string
}

export interface CardSummary {
  id: UUID
  name: string
  current_invoice_amount: string
  credit_limit: string
  available_limit: string
  closing_day: number
  due_day: number
}

export interface FinancingSummary {
  id: UUID
  name: string
  current_installment: number
  installments_total: number
  installments_remaining: number
  next_installment_amount: string | null
  next_installment_due_date: string | null
  outstanding_balance: string
  accumulated_savings: string
}

export interface MonthPoint {
  label: string
  year: number
  month: number
  income: string
  expenses: string
  gross_worth: string
  net_worth: string
  yield_amount: string
}

export interface CategoryExpense {
  category_id: UUID | null
  category_name: string
  amount: string
}

export interface YieldByAccount {
  account_id: UUID
  account_name: string
  institution_name: string
  amount: string
}

export interface Projection {
  horizon_days: number
  current_balance: string
  projected_balance: string
}

export interface Dashboard {
  summary: DashboardSummary
  accounts: AccountSummary[]
  cards: CardSummary[]
  financings: FinancingSummary[]
  income_vs_expenses: MonthPoint[]
  expenses_by_category: CategoryExpense[]
  worth_evolution: MonthPoint[]
  yield_evolution: MonthPoint[]
  yield_by_account: YieldByAccount[]
  projection_30d: Projection
}
