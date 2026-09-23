export function formatCurrency(value: number | string): string {
  const num = typeof value === "string" ? Number(value) : value
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(Number.isFinite(num) ? num : 0)
}

export function formatDate(value: string | Date | null | undefined): string {
  if (!value) return "—"
  // Datas puras ("YYYY-MM-DD") precisam de horário explícito para não serem
  // interpretadas em UTC e "voltarem" um dia no fuso local; datetimes completos
  // (com "T") já trazem essa informação e não devem ser modificados.
  const date = typeof value === "string" ? new Date(value.includes("T") ? value : `${value}T00:00:00`) : value
  return new Intl.DateTimeFormat("pt-BR").format(date)
}

export function formatPercent(value: number | string): string {
  const num = typeof value === "string" ? Number(value) : value
  return `${new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(
    Number.isFinite(num) ? num : 0,
  )}%`
}

export function monthLabel(month: number, year: number): string {
  const date = new Date(year, month - 1, 1)
  return new Intl.DateTimeFormat("pt-BR", { month: "short", year: "2-digit" }).format(date)
}

/** Data de hoje (YYYY-MM-DD) no fuso do navegador. `toISOString()` daria a data em UTC — no
 * Brasil (UTC-3), depois das 21h isso já é o dia seguinte e o lançamento cairia no mês errado. */
export function todayISO(): string {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const day = String(now.getDate()).padStart(2, "0")
  return `${now.getFullYear()}-${month}-${day}`
}
