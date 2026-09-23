import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query"
import { FileText, Pencil, Plus, ShoppingBag, Trash2 } from "lucide-react"
import { useState } from "react"
import { cardsApi } from "@/api/cards"
import { CardFormDialog } from "@/components/forms/CardFormDialog"
import { InvoicesDialog } from "@/components/forms/InvoicesDialog"
import { PurchaseFormDialog } from "@/components/forms/PurchaseFormDialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useToast } from "@/components/ui/toaster"
import { formatCurrency } from "@/lib/format"
import type { CreditCard } from "@/types"
import { invalidateFinancialData } from "@/lib/invalidate"
import { getApiErrorMessage } from "@/lib/api-error"

export function CardsPage() {
  const { data, isLoading } = useQuery({ queryKey: ["cards"], queryFn: cardsApi.list })
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<CreditCard | null>(null)
  const [purchaseOpen, setPurchaseOpen] = useState(false)
  const [invoicesOpen, setInvoicesOpen] = useState(false)
  const [activeCardId, setActiveCardId] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const { notify } = useToast()

  const deactivateMutation = useMutation({
    mutationFn: cardsApi.deactivate,
    onSuccess: () => {
      invalidateFinancialData(queryClient)
      notify({ title: "Cartão inativado.", variant: "success" })
    },
    onError: (err: unknown) => notify({ title: getApiErrorMessage(err, "Não foi possível concluir a ação."), variant: "error" }),
  })

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Cartões de crédito</h1>
          <p className="text-sm text-muted-foreground">Faturas, limites e compras parceladas</p>
        </div>
        <Button
          onClick={() => {
            setEditing(null)
            setFormOpen(true)
          }}
        >
          <Plus className="h-4 w-4" /> Novo cartão
        </Button>
      </div>

      {isLoading ? (
        <Skeleton className="h-48 w-full" />
      ) : !data || data.length === 0 ? (
        <p className="rounded-lg border border-border bg-card p-10 text-center text-sm text-muted-foreground">
          Nenhum cartão cadastrado ainda.
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((card) => (
            <Card key={card.id}>
              <CardContent className="flex flex-col gap-2 p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium">{card.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {card.brand} {card.last_digits ? `•••• ${card.last_digits}` : ""}
                    </p>
                  </div>
                  <Badge variant={card.active ? "success" : "secondary"}>{card.active ? "Ativo" : "Inativo"}</Badge>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Fatura atual</p>
                  <p className="font-mono-num text-xl font-semibold">{formatCurrency(card.current_invoice_amount)}</p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                  <span>Limite: {formatCurrency(card.credit_limit)}</span>
                  <span>Disponível: {formatCurrency(card.available_limit)}</span>
                  <span>Fecha dia {card.closing_day}</span>
                  <span>Vence dia {card.due_day}</span>
                </div>
                <div className="mt-2 flex flex-wrap gap-3 border-t border-border pt-2 text-xs">
                  <button
                    onClick={() => {
                      setActiveCardId(card.id)
                      setPurchaseOpen(true)
                    }}
                    className="flex items-center gap-1 text-muted-foreground hover:text-foreground"
                  >
                    <ShoppingBag className="h-3.5 w-3.5" /> Nova compra
                  </button>
                  <button
                    onClick={() => {
                      setActiveCardId(card.id)
                      setInvoicesOpen(true)
                    }}
                    className="flex items-center gap-1 text-muted-foreground hover:text-foreground"
                  >
                    <FileText className="h-3.5 w-3.5" /> Faturas
                  </button>
                  <button
                    onClick={() => {
                      setEditing(card)
                      setFormOpen(true)
                    }}
                    className="flex items-center gap-1 text-muted-foreground hover:text-foreground"
                  >
                    <Pencil className="h-3.5 w-3.5" /> Editar
                  </button>
                  {card.active && (
                    <button
                      onClick={() => window.confirm(`Inativar o cartão "${card.name}"?`) && deactivateMutation.mutate(card.id)}
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

      <CardFormDialog open={formOpen} onOpenChange={setFormOpen} card={editing} />
      <PurchaseFormDialog open={purchaseOpen} onOpenChange={setPurchaseOpen} cardId={activeCardId} />
      <InvoicesDialog open={invoicesOpen} onOpenChange={setInvoicesOpen} cardId={activeCardId} />
    </div>
  )
}
