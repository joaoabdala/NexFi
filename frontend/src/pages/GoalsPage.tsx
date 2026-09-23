import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Pencil, Plus, Trash2 } from "lucide-react"
import { useState } from "react"
import { goalsApi } from "@/api/planning"
import { GoalFormDialog } from "@/components/forms/GoalFormDialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useToast } from "@/components/ui/toaster"
import { formatCurrency, formatDate, formatPercent } from "@/lib/format"
import type { FinancialGoal } from "@/types"

export function GoalsPage() {
  const { data, isLoading } = useQuery({ queryKey: ["goals"], queryFn: goalsApi.list })
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<FinancialGoal | null>(null)
  const queryClient = useQueryClient()
  const { notify } = useToast()

  const removeMutation = useMutation({
    mutationFn: goalsApi.remove,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] })
      notify({ title: "Meta removida.", variant: "success" })
    },
  })

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Metas financeiras</h1>
          <p className="text-sm text-muted-foreground">Acompanhe o progresso dos seus objetivos</p>
        </div>
        <Button
          onClick={() => {
            setEditing(null)
            setDialogOpen(true)
          }}
        >
          <Plus className="h-4 w-4" /> Nova meta
        </Button>
      </div>

      {isLoading ? (
        <Skeleton className="h-48 w-full" />
      ) : !data || data.length === 0 ? (
        <p className="rounded-lg border border-border bg-card p-10 text-center text-sm text-muted-foreground">
          Nenhuma meta cadastrada ainda.
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((goal) => {
            const pct = Math.min(Number(goal.progress_percentage), 100)
            return (
              <Card key={goal.id}>
                <CardContent className="flex flex-col gap-2 p-4">
                  <div className="flex items-center justify-between">
                    <p className="font-medium">{goal.name}</p>
                    <span className="text-xs font-medium text-primary">{formatPercent(goal.progress_percentage)}</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
                    <div className="h-full rounded-full bg-primary" style={{ width: `${pct}%` }} />
                  </div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{formatCurrency(goal.current_amount)}</span>
                    <span>{formatCurrency(goal.target_amount)}</span>
                  </div>
                  {goal.target_date && (
                    <p className="text-xs text-muted-foreground">Meta para {formatDate(goal.target_date)}</p>
                  )}
                  <div className="mt-2 flex gap-3 border-t border-border pt-2 text-xs">
                    <button
                      onClick={() => {
                        setEditing(goal)
                        setDialogOpen(true)
                      }}
                      className="flex items-center gap-1 text-muted-foreground hover:text-foreground"
                    >
                      <Pencil className="h-3.5 w-3.5" /> Editar
                    </button>
                    <button
                      onClick={() => removeMutation.mutate(goal.id)}
                      className="flex items-center gap-1 text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 className="h-3.5 w-3.5" /> Remover
                    </button>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      <GoalFormDialog open={dialogOpen} onOpenChange={setDialogOpen} goal={editing} />
    </div>
  )
}
