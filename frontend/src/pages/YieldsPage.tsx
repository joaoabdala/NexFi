import { useQuery } from "@tanstack/react-query"
import { Plus, TrendingUp } from "lucide-react"
import { useState } from "react"
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { dashboardApi } from "@/api/dashboard"
import { TransactionFormDialog } from "@/components/forms/TransactionFormDialog"
import { KpiCard } from "@/components/KpiCard"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { formatCurrency } from "@/lib/format"

export function YieldsPage() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", "12m"],
    queryFn: () => dashboardApi.get("12m"),
  })

  const yearTotal = data?.yield_evolution.reduce((sum, p) => sum + Number(p.yield_amount), 0) ?? 0

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Rendimentos</h1>
          <p className="text-sm text-muted-foreground">Acompanhe o rendimento das suas contas e investimentos</p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4" /> Registrar rendimento
        </Button>
      </div>

      {isLoading || !data ? (
        <Skeleton className="h-48 w-full" />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
            <KpiCard label="Rendimento do mês" value={formatCurrency(data.summary.yield_month)} icon={TrendingUp} tone="positive" />
            <KpiCard label="Rendimento acumulado (12 meses)" value={formatCurrency(yearTotal)} icon={TrendingUp} tone="positive" />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Evolução mensal</CardTitle>
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

          <Card>
            <CardHeader>
              <CardTitle>Rendimento por conta (mês atual)</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              {data.yield_by_account.length === 0 ? (
                <p className="text-sm text-muted-foreground">Nenhum rendimento registrado neste mês.</p>
              ) : (
                data.yield_by_account.map((y) => (
                  <div key={y.account_id} className="flex items-center justify-between text-sm">
                    <span>
                      {y.institution_name} — {y.account_name}
                    </span>
                    <span className="font-mono-num font-medium">{formatCurrency(y.amount)}</span>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </>
      )}

      <TransactionFormDialog open={dialogOpen} onOpenChange={setDialogOpen} defaultType="RENDIMENTO" />
    </div>
  )
}
