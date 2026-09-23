import type { QueryClient } from "@tanstack/react-query"

/**
 * Tudo que pode mudar quando dinheiro se move (lançamento, transferência, ajuste, compra no
 * cartão, pagamento de fatura/parcela, amortização, recorrência). Invalidar só algumas chaves por
 * tela deixava saldos, metas vinculadas a contas e orçamentos desatualizados por até 30 s (ou até
 * trocar de página). Refazer umas poucas consultas a mais é barato; número errado na tela, não.
 */
const FINANCIAL_QUERY_KEYS = [
  "accounts",
  "transactions",
  "dashboard",
  "budgets",
  "budgets-summary",
  "goals",
  "cards",
  "invoices",
  "financing",
  "financing-installments",
  "recurrences",
] as const

export function invalidateFinancialData(queryClient: QueryClient) {
  for (const key of FINANCIAL_QUERY_KEYS) {
    void queryClient.invalidateQueries({ queryKey: [key] })
  }
}
