import { useQuery } from "@tanstack/react-query"
import { Bar, BarChart, CartesianGrid, LabelList, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { cardsApi } from "@/api/cards"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { formatCurrency, monthLabel } from "@/lib/format"
import type { InvoiceProjection } from "@/types"

// Paleta categórica validada (claro/escuro) em index.css. Ordem fixa, nunca reciclada: a partir do
// 6º cartão, os demais viram "Outros" — um 7º tom geraria cores parecidas demais entre si.
const MAX_SERIES = 6
const OTHERS_KEY = "__outros__"

const compactCurrency = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  notation: "compact",
  maximumFractionDigits: 1,
})

interface Series {
  key: string
  name: string
  color: string
}

function buildChart(projection: InvoiceProjection) {
  const cards = projection.cards
  const visible = cards.length > MAX_SERIES ? cards.slice(0, MAX_SERIES - 1) : cards
  const folded = new Set(cards.slice(visible.length).map((c) => c.id))

  const series: Series[] = visible.map((c, i) => ({ key: c.id, name: c.name, color: `var(--series-${i + 1})` }))
  if (folded.size > 0) series.push({ key: OTHERS_KEY, name: "Outros", color: `var(--series-${MAX_SERIES})` })

  const rows = projection.months.map((m) => {
    const row: Record<string, number | string> = { label: monthLabel(m.month, m.year), total: Number(m.total) }
    for (const s of series) row[s.key] = 0
    for (const [cardId, amount] of Object.entries(m.by_card)) {
      const key = folded.has(cardId) ? OTHERS_KEY : cardId
      row[key] = Number(row[key] ?? 0) + Number(amount)
    }
    return row
  })
  return { series, rows }
}

/** Faturas de cartão a pagar nos próximos 12 meses (pelo mês de vencimento), empilhadas por cartão. */
export function InvoiceProjectionChart() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["invoice-projection"],
    queryFn: () => cardsApi.invoiceProjection(12),
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Faturas previstas — próximos 12 meses</CardTitle>
        <p className="text-xs text-muted-foreground">
          Quanto falta pagar de cartão em cada mês de vencimento, incluindo as parcelas futuras das compras parceladas.
        </p>
      </CardHeader>
      <CardContent>
        {isLoading && <Skeleton className="h-72 w-full" />}
        {isError && <p className="text-sm text-muted-foreground">Não foi possível carregar a projeção de faturas.</p>}
        {data && <ChartBody projection={data} />}
      </CardContent>
    </Card>
  )
}

function ChartBody({ projection }: { projection: InvoiceProjection }) {
  const { series, rows } = buildChart(projection)
  if (series.length === 0) {
    return <p className="py-10 text-center text-sm text-muted-foreground">Nenhuma fatura em aberto nos próximos meses.</p>
  }

  return (
    <>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 20, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="var(--muted-foreground)" />
            <YAxis
              tick={{ fontSize: 12 }}
              stroke="var(--muted-foreground)"
              width={70}
              tickFormatter={(v: number) => compactCurrency.format(v)}
            />
            <Tooltip cursor={{ fill: "var(--muted)", opacity: 0.4 }} content={<ProjectionTooltip series={series} />} />
            {/* Texto da legenda na tinta de texto; a cor da série fica só no marcador ao lado. */}
            <Legend formatter={(value) => <span style={{ color: "var(--foreground)" }}>{value}</span>} />
            {series.map((s, index) => (
              <Bar
                key={s.key}
                dataKey={s.key}
                name={s.name}
                stackId="faturas"
                fill={s.color}
                // Contorno na cor da superfície: 2px de separação entre os segmentos empilhados.
                stroke="var(--card)"
                strokeWidth={2}
                maxBarSize={48}
              >
                {index === series.length - 1 && (
                  <LabelList
                    dataKey="total"
                    position="top"
                    // Total do mês acima da pilha, em tinta de texto (não na cor da série).
                    formatter={(v: unknown) => (Number(v) > 0 ? compactCurrency.format(Number(v)) : "")}
                    style={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                  />
                )}
              </Bar>
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Visão em tabela: acessível a leitores de tela e a quem não distingue as cores. */}
      <details className="mt-3 text-sm">
        <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">Ver valores em tabela</summary>
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-muted-foreground">
                <th className="py-1 pr-3 font-medium">Mês</th>
                {series.map((s) => (
                  <th key={s.key} className="py-1 pr-3 text-right font-medium">{s.name}</th>
                ))}
                <th className="py-1 text-right font-medium">Total</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={String(row.label)} className="border-t border-border">
                  <td className="py-1 pr-3">{row.label}</td>
                  {series.map((s) => (
                    <td key={s.key} className="font-mono-num py-1 pr-3 text-right">
                      {Number(row[s.key]) > 0 ? formatCurrency(Number(row[s.key])) : "—"}
                    </td>
                  ))}
                  <td className="font-mono-num py-1 text-right font-medium">{formatCurrency(Number(row.total))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </>
  )
}


interface TooltipProps {
  active?: boolean
  label?: string | number
  payload?: { payload: Record<string, number | string> }[]
  series: Series[]
}

/** Mês + total no topo; só os cartões com valor naquele mês, do maior para o menor. */
function ProjectionTooltip({ active, label, payload, series }: TooltipProps) {
  if (!active || !payload?.length) return null
  const row = payload[0].payload
  const items = series
    .map((s) => ({ ...s, value: Number(row[s.key] ?? 0) }))
    .filter((s) => s.value > 0)
    .sort((a, b) => b.value - a.value)
  return (
    <div className="rounded-md border border-border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-md">
      <p className="mb-1 font-medium">
        {label} · <span className="font-mono-num">{formatCurrency(Number(row.total))}</span>
      </p>
      {items.length === 0 && <p className="text-muted-foreground">Nenhuma fatura neste mês</p>}
      {items.map((item) => (
        <p key={item.key} className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: item.color }} />
            {item.name}
          </span>
          <span className="font-mono-num">{formatCurrency(item.value)}</span>
        </p>
      ))}
    </div>
  )
}
