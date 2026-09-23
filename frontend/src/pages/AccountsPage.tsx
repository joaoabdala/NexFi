import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Pencil, Plus, Scale, Trash2 } from "lucide-react"
import { useState } from "react"
import { accountsApi } from "@/api/accounts"
import { AccountFormDialog } from "@/components/forms/AccountFormDialog"
import { BalanceAdjustmentDialog } from "@/components/forms/BalanceAdjustmentDialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useToast } from "@/components/ui/toaster"
import { useAccounts } from "@/hooks/useReferenceData"
import { formatCurrency } from "@/lib/format"
import type { Account } from "@/types"

const TYPE_LABELS: Record<string, string> = {
  CONTA_CORRENTE: "Conta corrente",
  CONTA_DIGITAL: "Conta digital",
  POUPANCA: "Poupança",
  DINHEIRO: "Dinheiro",
  COFRINHO_RESERVA: "Cofrinho / Reserva",
  INVESTIMENTO: "Investimento",
  OUTROS: "Outros",
}

export function AccountsPage() {
  const { data, isLoading } = useAccounts()
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Account | null>(null)
  const [adjustOpen, setAdjustOpen] = useState(false)
  const [adjustingAccount, setAdjustingAccount] = useState<Account | null>(null)
  const queryClient = useQueryClient()
  const { notify } = useToast()

  const deactivateMutation = useMutation({
    mutationFn: accountsApi.deactivate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      notify({ title: "Conta inativada.", variant: "success" })
    },
  })

  const total = data?.reduce((sum, a) => sum + Number(a.current_balance), 0) ?? 0

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Contas</h1>
          <p className="text-sm text-muted-foreground">Saldo consolidado: {formatCurrency(total)}</p>
        </div>
        <Button
          onClick={() => {
            setEditing(null)
            setFormOpen(true)
          }}
        >
          <Plus className="h-4 w-4" /> Nova conta
        </Button>
      </div>

      {isLoading ? (
        <Skeleton className="h-48 w-full" />
      ) : !data || data.length === 0 ? (
        <p className="rounded-lg border border-border bg-card p-10 text-center text-sm text-muted-foreground">
          Nenhuma conta cadastrada ainda.
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((account) => (
            <Card key={account.id}>
              <CardContent className="flex flex-col gap-2 p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium">{account.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {account.institution_name} · {TYPE_LABELS[account.type]}
                    </p>
                  </div>
                  <Badge variant={account.active ? "success" : "secondary"}>
                    {account.active ? "Ativa" : "Inativa"}
                  </Badge>
                </div>
                <p className="font-mono-num text-xl font-semibold">{formatCurrency(account.current_balance)}</p>
                <div className="flex flex-wrap gap-1">
                  {account.include_in_available_worth && <Badge variant="outline">Disponível</Badge>}
                  {account.include_in_invested_worth && <Badge variant="outline">Investido</Badge>}
                </div>
                <div className="mt-2 flex gap-3 border-t border-border pt-2 text-xs">
                  <button
                    onClick={() => {
                      setAdjustingAccount(account)
                      setAdjustOpen(true)
                    }}
                    className="flex items-center gap-1 text-muted-foreground hover:text-foreground"
                  >
                    <Scale className="h-3.5 w-3.5" /> Ajustar saldo
                  </button>
                  <button
                    onClick={() => {
                      setEditing(account)
                      setFormOpen(true)
                    }}
                    className="flex items-center gap-1 text-muted-foreground hover:text-foreground"
                  >
                    <Pencil className="h-3.5 w-3.5" /> Editar
                  </button>
                  {account.active && (
                    <button
                      onClick={() => deactivateMutation.mutate(account.id)}
                      className="flex items-center gap-1 text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 className="h-3.5 w-3.5" /> Inativar
                    </button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <AccountFormDialog open={formOpen} onOpenChange={setFormOpen} account={editing} />
      <BalanceAdjustmentDialog open={adjustOpen} onOpenChange={setAdjustOpen} account={adjustingAccount} />
    </div>
  )
}
