import { isAxiosError } from "axios"

interface ValidationIssue {
  msg?: string
}

/**
 * Mensagem legível de um erro da API. O FastAPI devolve `detail` como string nas regras de
 * negócio, mas como LISTA de objetos nos erros de validação (422) — renderizar essa lista direto
 * num toast derruba o React ("Objects are not valid as a React child").
 */
export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (!isAxiosError(error)) return fallback
  if (!error.response) return "Sem conexão com o servidor. Tente novamente."
  const detail: unknown = error.response.data?.detail
  if (typeof detail === "string" && detail.trim()) return detail
  if (Array.isArray(detail)) {
    const first = (detail as ValidationIssue[]).find((issue) => typeof issue?.msg === "string")
    if (first?.msg) return `Dados inválidos: ${first.msg.replace(/^Value error, /, "")}`
  }
  return fallback
}
