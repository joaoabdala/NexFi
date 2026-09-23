import { useQuery } from "@tanstack/react-query"
import { Plus } from "lucide-react"
import { useState } from "react"
import { budgetsApi } from "@/api/planning"
import { BudgetFormDialog } from "@/components/forms/BudgetFormDialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import { formatCurrency, formatPercent } from "@/lib/format"

export function BudgetsPage() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const today = new Date()
  const { data, isLoading } = useQuery({
    queryKey: ["budgets-summary", today.getFullYear(), today.getMonth() + 1],
    queryFn: () => budgetsApi.summary(today.getFullYear(), today.getMonth() + 1),
  })

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Orçamentos</h1>
          <p className="text-sm text-muted-foreground">
            {new Intl.DateTimeFormat("pt-BR", { month: "long", year: "numeric" }).format(today)}
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4" /> Novo orçamento
        </Button>
      </div>

      {isLoading ? (
        <Skeleton className="h-48 w-full" />
      ) : !data || data.length === 0 ? (
        <p className="rounded-lg border border-border bg-card p-10 text-center text-sm text-muted-foreground">
          Nenhum orçamento cadastrado para este mês.
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((item) => {
            const pct = Math.min(Number(item.percentage_used), 100)
            const over = Number(item.percentage_used) >= 100
            return (
              <Card key={item.category_id}>
                <CardContent className="flex flex-col gap-2 p-4">
                  <div className="flex items-center justify-between">
                    <p className="font-medium">{item.category_name}</p>
                    <span className={cn("text-xs font-medium", over ? "text-destructive" : "text-muted-foreground")}>
                      {formatPercent(item.percentage_used)}
                    </span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
                    <div
                      className={cn("h-full rounded-full", over ? "bg-destructive" : "bg-primary")}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-1 text-xs text-muted-foreground">
                    <div>
                      <p>Orçamento</p>
                      <p className="font-mono-num font-medium text-foreground">{formatCurrency(item.budget_amount)}</p>
                    </div>
                    <div>
                      <p>Realizado</p>
                      <p className="font-mono-num font-medium text-foreground">{formatCurrency(item.realized_amount)}</p>
                    </div>
                    <div>
                      <p>Restante</p>
                      <p className="font-mono-num font-medium text-foreground">{formatCurrency(item.remaining_amount)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      <BudgetFormDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </div>
  )
}
