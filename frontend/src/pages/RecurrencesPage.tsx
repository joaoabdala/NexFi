import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Pencil, Plus, RefreshCw, Trash2 } from "lucide-react"
import { useState } from "react"
import { recurrencesApi } from "@/api/planning"
import { RecurrenceEditDialog } from "@/components/forms/RecurrenceEditDialog"
import { RecurrenceFormDialog } from "@/components/forms/RecurrenceFormDialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useToast } from "@/components/ui/toaster"
import { formatCurrency } from "@/lib/format"
import type { RecurrenceRule } from "@/types"
import { invalidateFinancialData } from "@/lib/invalidate"
import { getApiErrorMessage } from "@/lib/api-error"

const FREQUENCY_LABEL: Record<string, string> = {
  SEMANAL: "Semanal",
  MENSAL: "Mensal",
  ANUAL: "Anual",
  PERSONALIZADA: "Personalizada",
}

export function RecurrencesPage() {
  const { data, isLoading } = useQuery({ queryKey: ["recurrences"], queryFn: recurrencesApi.list })
  const [createOpen, setCreateOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<RecurrenceRule | null>(null)
  const queryClient = useQueryClient()
  const { notify } = useToast()

  const removeMutation = useMutation({
    mutationFn: recurrencesApi.remove,
    onSuccess: () => {
      invalidateFinancialData(queryClient)
      notify({ title: "Recorrência inativada.", variant: "success" })
    },
    onError: (err: unknown) => notify({ title: getApiErrorMessage(err, "Não foi possível concluir a ação."), variant: "error" }),
  })

  const generateMutation = useMutation({
    mutationFn: recurrencesApi.generate,
    onSuccess: () => {
      invalidateFinancialData(queryClient)
      notify({ title: "Transações futuras geradas.", variant: "success" })
    },
  })

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Recorrências</h1>
          <p className="text-sm text-muted-foreground">Receitas e despesas que se repetem automaticamente</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => generateMutation.mutate()}>
            <RefreshCw className="h-4 w-4" /> Gerar transações
          </Button>
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" /> Nova recorrência
          </Button>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card">
        {isLoading ? (
          <div className="p-4">
            <Skeleton className="h-40 w-full" />
          </div>
        ) : !data || data.length === 0 ? (
          <p className="p-10 text-center text-sm text-muted-foreground">Nenhuma recorrência cadastrada.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Descrição</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Frequência</TableHead>
                <TableHead className="text-right">Valor</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-16" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((rule) => (
                <TableRow key={rule.id}>
                  <TableCell className="font-medium">{rule.description}</TableCell>
                  <TableCell>{rule.type === "RECEITA" ? "Receita" : "Despesa"}</TableCell>
                  <TableCell>{FREQUENCY_LABEL[rule.frequency]}</TableCell>
                  <TableCell className="font-mono-num text-right">{formatCurrency(rule.amount)}</TableCell>
                  <TableCell>
                    <Badge variant={rule.active ? "success" : "secondary"}>{rule.active ? "Ativa" : "Inativa"}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setEditingRule(rule)}
                        className="text-muted-foreground hover:text-foreground"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      {rule.active && (
                        <button
                          onClick={() => window.confirm(`Excluir a recorrência "${rule.description}"? Os lançamentos futuros pendentes dela serão cancelados.`) && removeMutation.mutate(rule.id)}
                          className="text-muted-foreground hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      <RecurrenceFormDialog open={createOpen} onOpenChange={setCreateOpen} />
      <RecurrenceEditDialog
        open={!!editingRule}
        onOpenChange={(v) => !v && setEditingRule(null)}
        rule={editingRule}
      />
    </div>
  )
}
