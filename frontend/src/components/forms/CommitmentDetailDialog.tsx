import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { financingApi } from "@/api/financing"
import { AmortizationFormDialog } from "@/components/forms/AmortizationFormDialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/components/ui/toaster"
import { useAccounts } from "@/hooks/useReferenceData"
import { formatCurrency, formatDate, todayISO } from "@/lib/format"
import type { CommitmentInstallmentStatus } from "@/types"

const STATUS_VARIANT: Record<CommitmentInstallmentStatus, "success" | "warning" | "destructive" | "secondary"> = {
  PENDENTE: "secondary",
  PAGA: "success",
  AMORTIZADA: "warning",
  CANCELADA: "destructive",
}

export function CommitmentDetailDialog({
  open,
  onOpenChange,
  commitmentId,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  commitmentId: string | null
}) {
  const { data: accounts } = useAccounts()
  const [payAccount, setPayAccount] = useState<string>("")
  const [amortizationOpen, setAmortizationOpen] = useState(false)
  const queryClient = useQueryClient()
  const { notify } = useToast()

  const { data: installments, isLoading } = useQuery({
    queryKey: ["financing-installments", commitmentId],
    queryFn: () => financingApi.listInstallments(commitmentId!),
    enabled: open && !!commitmentId,
  })

  const payMutation = useMutation({
    mutationFn: (installmentId: string) =>
      financingApi.payInstallment(commitmentId!, installmentId, {
        payment_date: todayISO(),
        account_id: payAccount,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["financing-installments"] })
      queryClient.invalidateQueries({ queryKey: ["financing"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      notify({ title: "Parcela paga.", variant: "success" })
    },
    onError: () => notify({ title: "Selecione uma conta e tente novamente.", variant: "error" }),
  })

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Parcelas do financiamento</DialogTitle>
          </DialogHeader>

          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Conta para pagamento:</span>
              <Select value={payAccount} onValueChange={setPayAccount}>
                <SelectTrigger className="w-56">
                  <SelectValue placeholder="Selecione a conta" />
                </SelectTrigger>
                <SelectContent>
                  {accounts?.map((a) => (
                    <SelectItem key={a.id} value={a.id}>
                      {a.institution_name} — {a.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button variant="outline" size="sm" onClick={() => setAmortizationOpen(true)}>
              Amortizar
            </Button>
          </div>

          <div className="flex max-h-[50vh] flex-col gap-1.5 overflow-y-auto scrollbar-thin">
            {isLoading && <p className="text-sm text-muted-foreground">Carregando…</p>}
            {installments?.map((installment) => (
              <div
                key={installment.id}
                className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm"
              >
                <div>
                  <p className="font-medium">
                    {installment.number} — {formatDate(installment.due_date)}
                  </p>
                  <p className="text-xs text-muted-foreground">{formatCurrency(installment.updated_amount)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={STATUS_VARIANT[installment.status]}>{installment.status}</Badge>
                  {installment.status === "PENDENTE" && (
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={!payAccount || payMutation.isPending}
                      onClick={() => payMutation.mutate(installment.id)}
                    >
                      Pagar
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
      <AmortizationFormDialog open={amortizationOpen} onOpenChange={setAmortizationOpen} commitmentId={commitmentId} />
    </>
  )
}
