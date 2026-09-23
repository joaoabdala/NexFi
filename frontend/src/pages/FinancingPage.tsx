import { useQuery } from "@tanstack/react-query"
import { ListOrdered, Plus } from "lucide-react"
import { useState } from "react"
import { financingApi } from "@/api/financing"
import { CommitmentDetailDialog } from "@/components/forms/CommitmentDetailDialog"
import { CommitmentFormDialog } from "@/components/forms/CommitmentFormDialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { formatCurrency, formatDate } from "@/lib/format"

const TYPE_LABEL: Record<string, string> = {
  FINANCIAMENTO: "Financiamento",
  EMPRESTIMO: "Empréstimo",
  CONSORCIO: "Consórcio",
  OUTROS: "Outros",
}

export function FinancingPage() {
  const { data, isLoading } = useQuery({ queryKey: ["financing"], queryFn: financingApi.list })
  const [formOpen, setFormOpen] = useState(false)
  const [detailOpen, setDetailOpen] = useState(false)
  const [activeId, setActiveId] = useState<string | null>(null)

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Financiamentos</h1>
          <p className="text-sm text-muted-foreground">Parcelas, pagamentos e amortizações</p>
        </div>
        <Button onClick={() => setFormOpen(true)}>
          <Plus className="h-4 w-4" /> Novo financiamento
        </Button>
      </div>

      {isLoading ? (
        <Skeleton className="h-48 w-full" />
      ) : !data || data.length === 0 ? (
        <p className="rounded-lg border border-border bg-card p-10 text-center text-sm text-muted-foreground">
          Nenhum financiamento cadastrado.
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((commitment) => (
            <Card key={commitment.id}>
              <CardContent className="flex flex-col gap-2 p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium">{commitment.name}</p>
                    <p className="text-xs text-muted-foreground">{TYPE_LABEL[commitment.type]}</p>
                  </div>
                  <Badge variant={commitment.status === "ATIVO" ? "success" : "secondary"}>
                    {commitment.status}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  Parcela {commitment.installments_paid + commitment.installments_amortized + 1}/
                  {commitment.installments_total} · {commitment.installments_remaining} restantes ·{" "}
                  {commitment.installments_amortized} amortizadas
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Saldo devedor</span>
                  <span className="font-mono-num font-medium">{formatCurrency(commitment.outstanding_balance)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Próxima parcela</span>
                  <span className="font-mono-num text-sm">
                    {commitment.next_installment
                      ? `${formatCurrency(commitment.next_installment.updated_amount)} · ${formatDate(
                          commitment.next_installment.due_date,
                        )}`
                      : "—"}
                  </span>
                </div>
                {Number(commitment.accumulated_savings) > 0 && (
                  <Badge variant="success" className="w-fit">
                    Economia acumulada: {formatCurrency(commitment.accumulated_savings)}
                  </Badge>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2"
                  onClick={() => {
                    setActiveId(commitment.id)
                    setDetailOpen(true)
                  }}
                >
                  <ListOrdered className="h-4 w-4" /> Ver parcelas
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <CommitmentFormDialog open={formOpen} onOpenChange={setFormOpen} />
      <CommitmentDetailDialog open={detailOpen} onOpenChange={setDetailOpen} commitmentId={activeId} />
    </div>
  )
}
