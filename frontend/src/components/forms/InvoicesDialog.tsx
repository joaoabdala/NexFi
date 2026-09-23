import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { invoicesApi } from "@/api/cards"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { useToast } from "@/components/ui/toaster"
import { formatCurrency, formatDate, todayISO } from "@/lib/format"
import type { CreditCardInvoice, InvoiceStatus } from "@/types"
import { getApiErrorMessage } from "@/lib/api-error"
import { invalidateFinancialData } from "@/lib/invalidate"

const STATUS_VARIANT: Record<InvoiceStatus, "success" | "warning" | "destructive" | "secondary"> = {
  ABERTA: "secondary",
  FECHADA: "warning",
  VENCIDA: "destructive",
  PAGA: "success",
}

export function InvoicesDialog({
  open,
  onOpenChange,
  cardId,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  cardId: string | null
}) {
  const [expanded, setExpanded] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const { notify } = useToast()

  const { data, isLoading } = useQuery({
    queryKey: ["invoices", cardId],
    queryFn: () => invoicesApi.list(cardId!),
    enabled: open && !!cardId,
  })

  const payMutation = useMutation({
    mutationFn: (invoiceId: string) => invoicesApi.pay(invoiceId, { payment_date: todayISO() }),
    onSuccess: () => {
      invalidateFinancialData(queryClient)
      notify({ title: "Fatura paga.", variant: "success" })
    },
    onError: (err: unknown) => notify({ title: getApiErrorMessage(err, "Não foi possível pagar a fatura."), variant: "error" }),
  })

  const undoMutation = useMutation({
    mutationFn: (invoiceId: string) => invoicesApi.undoPayment(invoiceId),
    onSuccess: () => {
      invalidateFinancialData(queryClient)
      notify({ title: "Pagamento desfeito. O valor voltou para a conta.", variant: "success" })
    },
    onError: (err: unknown) => notify({ title: getApiErrorMessage(err, "Não foi possível desfazer o pagamento."), variant: "error" }),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Faturas</DialogTitle>
        </DialogHeader>
        <div className="flex max-h-[60vh] flex-col gap-2 overflow-y-auto scrollbar-thin">
          {isLoading && <p className="text-sm text-muted-foreground">Carregando…</p>}
          {!isLoading && (!data || data.length === 0) && (
            <p className="text-sm text-muted-foreground">Nenhuma fatura ainda.</p>
          )}
          {data?.map((invoice: CreditCardInvoice) => {
            const remaining = Number(invoice.amount) - Number(invoice.paid_amount ?? 0)
            const partiallyPaid = invoice.status !== "PAGA" && Number(invoice.paid_amount ?? 0) > 0
            return (
            <div key={invoice.id} className="rounded-md border border-border p-3 text-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{formatDate(invoice.competence)}</p>
                  <p className="text-xs text-muted-foreground">
                    Fecha {formatDate(invoice.closing_date)} · Vence {formatDate(invoice.due_date)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={STATUS_VARIANT[invoice.status]}>{invoice.status}</Badge>
                  <span className="font-mono-num font-medium">{formatCurrency(invoice.amount)}</span>
                </div>
              </div>
              {partiallyPaid && (
                <p className="mt-1 text-xs text-muted-foreground">
                  Já pago {formatCurrency(invoice.paid_amount)} · falta {formatCurrency(remaining)} (compra lançada depois do pagamento)
                </p>
              )}
              <div className="mt-2 flex items-center gap-3">
                <button
                  className="text-xs text-muted-foreground hover:text-foreground"
                  onClick={() => setExpanded(expanded === invoice.id ? null : invoice.id)}
                >
                  {expanded === invoice.id ? "Ocultar itens" : `Ver itens (${invoice.installments.length})`}
                </button>
                {invoice.status !== "PAGA" && remaining > 0 && (
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={payMutation.isPending}
                    onClick={() => {
                      const confirmed = window.confirm(
                        `Pagar a fatura de ${formatDate(invoice.competence)} no valor de ${formatCurrency(remaining)}? ` +
                          "O valor será debitado da conta de pagamento do cartão com a data de hoje.",
                      )
                      if (confirmed) payMutation.mutate(invoice.id)
                    }}
                  >
                    Pagar fatura
                  </Button>
                )}
                {Number(invoice.paid_amount ?? 0) > 0 && (
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={undoMutation.isPending}
                    onClick={() => {
                      const confirmed = window.confirm(
                        `Desfazer o último pagamento da fatura de ${formatDate(invoice.competence)}? ` +
                          "O valor volta para a conta e a fatura fica em aberto de novo.",
                      )
                      if (confirmed) undoMutation.mutate(invoice.id)
                    }}
                  >
                    Desfazer pagamento
                  </Button>
                )}
              </div>
              {expanded === invoice.id && (
                <div className="mt-2 flex flex-col gap-1 border-t border-border pt-2">
                  {invoice.installments.map((item) => (
                    <div key={item.id} className="flex items-center justify-between text-xs">
                      <span>
                        {item.description}
                        {item.installments_total && item.installments_total > 1
                          ? ` (${item.number}/${item.installments_total})`
                          : ""}
                      </span>
                      <span className="font-mono-num">{formatCurrency(item.amount)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            )
          })}
        </div>
      </DialogContent>
    </Dialog>
  )
}
