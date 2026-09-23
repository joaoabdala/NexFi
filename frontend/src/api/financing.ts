import { api } from "@/lib/api"
import type {
  Amortization,
  AmortizationType,
  CommitmentInstallment,
  CommitmentType,
  FinancialCommitment,
} from "@/types"

export interface CommitmentInput {
  institution_id: string
  type: CommitmentType
  name: string
  asset_value?: number | null
  down_payment?: number | null
  financed_amount: number
  interest_rate?: number | null
  installments_total: number
  default_installment_amount: number
  start_date: string
  due_day: number
  note?: string | null
}

export interface AmortizationInput {
  date: string
  paid_amount: number
  type: AmortizationType
  account_id: string
  installment_numbers?: number[] | null
  note?: string | null
}

export const financingApi = {
  list: () => api.get<FinancialCommitment[]>("/financing").then((r) => r.data),
  get: (id: string) => api.get<FinancialCommitment>(`/financing/${id}`).then((r) => r.data),
  create: (payload: CommitmentInput) => api.post<FinancialCommitment>("/financing", payload).then((r) => r.data),
  listInstallments: (id: string) =>
    api.get<CommitmentInstallment[]>(`/financing/${id}/installments`).then((r) => r.data),
  payInstallment: (
    commitmentId: string,
    installmentId: string,
    payload: { payment_date: string; account_id: string; paid_amount?: number | null },
  ) =>
    api
      .post<CommitmentInstallment>(
        `/financing/${commitmentId}/installments/${installmentId}/pay`,
        payload,
      )
      .then((r) => r.data),
  undoInstallmentPayment: (commitmentId: string, installmentId: string) =>
    api
      .post<CommitmentInstallment>(`/financing/${commitmentId}/installments/${installmentId}/undo-payment`)
      .then((r) => r.data),
}

export const amortizationsApi = {
  list: (commitmentId: string) =>
    api.get<Amortization[]>(`/amortizations/commitments/${commitmentId}`).then((r) => r.data),
  create: (commitmentId: string, payload: AmortizationInput) =>
    api.post<Amortization>(`/amortizations/commitments/${commitmentId}`, payload).then((r) => r.data),
}
