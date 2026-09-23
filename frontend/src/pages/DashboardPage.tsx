import { useQuery } from "@tanstack/react-query"
import {
  ArrowDownCircle,
  ArrowUpCircle,
  Landmark,
  PiggyBank,
  Scale,
  TrendingUp,
  Wallet,
} from "lucide-react"
import { useState } from "react"
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { dashboardApi } from "@/api/dashboard"
import { KpiCard } from "@/components/KpiCard"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { formatCurrency, formatDate } from "@/lib/format"
import { LoadError } from "@/components/LoadError"

const PERIODS = [
  { value: "3m", label: "3 meses" },
  { value: "6m", label: "6 meses" },
  { value: "12m", label: "12 meses" },
  { value: "current_year", label: "Ano atual" },
]

const PIE_COLORS = ["#14BBA6", "#5EEEA4", "#94A3B8", "#0e9484", "#1f2937", "#38bdf8", "#f59e0b", "#a855f7"]

export function DashboardPage() {
  const [period, setPeriod] = useState("6m")
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["dashboard", period],
    queryFn: () => dashboardApi.get(period),
  })

  if (isError) return <LoadError onRetry={() => void refetch()} message="Não foi possível carregar o dashboard." />

  if (isLoading || !data) {
    return (
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
    )
  }

  const { summary } = data

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">Visão consolidada da sua vida financeira</p>
        </div>
        <Select value={period} onValueChange={setPeriod}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {PERIODS.map((p) => (
              <SelectItem key={p.value} value={p.value}>
                {p.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard label="Saldo disponível" value={formatCurrency(summary.available_balance)} icon={Wallet} />
        <KpiCard label="Receitas do mês" value={formatCurrency(summary.income_month)} icon={ArrowUpCircle} tone="positive" />
        <KpiCard label="Despesas do mês" value={formatCurrency(summary.expenses_month)} icon={ArrowDownCircle} tone="negative" />
        <KpiCard
          label="Resultado do mês"
          value={formatCurrency(summary.result_month)}
          icon={Scale}
          tone={Number(summary.result_month) >= 0 ? "positive" : "negative"}
        />
        <KpiCard label="Patrimônio bruto" value={formatCurrency(summary.gross_worth)} icon={Landmark} />
        <KpiCard label="Patrimônio líquido" value={formatCurrency(summary.net_worth)} icon={PiggyBank} />
        <KpiCard label="Rendimentos do mês" value={formatCurrency(summary.yield_month)} icon={TrendingUp} tone="positive" />
        <KpiCard
          label="Projeção 30 dias"
          value={formatCurrency(data.projection_30d.projected_balance)}
          icon={Wallet}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Contas</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {data.accounts.length === 0 && <EmptyState text="Nenhuma conta cadastrada ainda." />}
            {data.accounts.map((a) => (
              <div key={a.id} className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm">
                <div>
                  <p className="font-medium">{a.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {a.institution_name} · {a.type.replaceAll("_", " ")}
                  </p>
                </div>
                <span className="font-mono-num font-medium">{formatCurrency(a.balance)}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Cartões</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {data.cards.length === 0 && <EmptyState text="Nenhum cartão cadastrado." />}
            {data.cards.map((c) => (
              <div key={c.id} className="rounded-md border border-border px-3 py-2 text-sm">
                <div className="flex items-center justify-between">
                  <p className="font-medium">{c.name}</p>
                  <span className="font-mono-num">{formatCurrency(c.current_invoice_amount)}</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Limite disp.: {formatCurrency(c.available_limit)} · Fecha dia {c.closing_day} · Vence dia {c.due_day}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {data.financings.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Financiamentos</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.financings.map((f) => (
              <div key={f.id} className="rounded-md border border-border p-3 text-sm">
                <p className="font-medium">{f.name}</p>
                <p className="text-xs text-muted-foreground">
                  Parcela {f.current_installment}/{f.installments_total} · {f.installments_remaining} restantes
                </p>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Saldo devedor</span>
                  <span className="font-mono-num font-medium">{formatCurrency(f.outstanding_balance)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Próxima parcela</span>
                  <span className="font-mono-num">
                    {f.next_installment_amount ? formatCurrency(f.next_installment_amount) : "—"}
                    {f.next_installment_due_date ? ` · ${formatDate(f.next_installment_due_date)}` : ""}
                  </span>
                </div>
                {Number(f.accumulated_savings) > 0 && (
                  <Badge variant="success" className="mt-2">
                    Economia acumulada: {formatCurrency(f.accumulated_savings)}
                  </Badge>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Receitas x Despesas</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.income_vs_expenses}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="var(--muted-foreground)" />
                <YAxis tick={{ fontSize: 12 }} stroke="var(--muted-foreground)" width={70} />
                <Tooltip formatter={(v) => formatCurrency(v as number)} />
                <Legend />
                <Bar dataKey="income" name="Receitas" fill="#14BBA6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="expenses" name="Despesas" fill="#94A3B8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Despesas por categoria (mês atual)</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            {data.expenses_by_category.length === 0 ? (
              <EmptyState text="Sem despesas no período." />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    // A API manda Decimal como string ("1.50"); o Pie do Recharts soma só valores
                    // numéricos e, com strings, o total dá 0 e nenhuma fatia é desenhada.
                    data={data.expenses_by_category.map((e) => ({ ...e, amount: Number(e.amount) }))}
                    dataKey="amount"
                    nameKey="category_name"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={2}
                  >
                    {data.expenses_by_category.map((entry, index) => (
                      <Cell key={entry.category_name} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => formatCurrency(v as number)} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Evolução patrimonial</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.worth_evolution}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="var(--muted-foreground)" />
                <YAxis tick={{ fontSize: 12 }} stroke="var(--muted-foreground)" width={70} />
                <Tooltip formatter={(v) => formatCurrency(v as number)} />
                <Legend />
                <Area type="monotone" dataKey="gross_worth" name="Patrimônio bruto" stroke="#14BBA6" fill="#14BBA6" fillOpacity={0.15} />
                <Area type="monotone" dataKey="net_worth" name="Patrimônio líquido" stroke="#5EEEA4" fill="#5EEEA4" fillOpacity={0.15} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Rendimentos</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.yield_evolution}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="var(--muted-foreground)" />
                <YAxis tick={{ fontSize: 12 }} stroke="var(--muted-foreground)" width={70} />
                <Tooltip formatter={(v) => formatCurrency(v as number)} />
                <Line type="monotone" dataKey="yield_amount" name="Rendimento" stroke="#14BBA6" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {data.yield_by_account.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Rendimentos por conta (mês atual)</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {data.yield_by_account.map((y) => (
              <div key={y.account_id} className="flex items-center justify-between text-sm">
                <span>
                  {y.institution_name} — {y.account_name}
                </span>
                <span className="font-mono-num font-medium">{formatCurrency(y.amount)}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function EmptyState({ text }: { text: string }) {
  return <p className="flex h-full items-center justify-center text-sm text-muted-foreground">{text}</p>
}
