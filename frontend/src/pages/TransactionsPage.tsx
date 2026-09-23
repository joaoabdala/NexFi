import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query"
import { ArrowLeftRight, Plus, Search, Undo2, X } from "lucide-react"
import { useEffect, useState } from "react"
import { transactionsApi, type TransactionFilters } from "@/api/transactions"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useToast } from "@/components/ui/toaster"
import { TransactionFormDialog } from "@/components/forms/TransactionFormDialog"
import { TransferFormDialog } from "@/components/forms/TransferFormDialog"
import { flattenCategories, useAccounts, useCategories } from "@/hooks/useReferenceData"
import { formatCurrency, formatDate } from "@/lib/format"
import type { TransactionStatus, TransactionType } from "@/types"
import { getApiErrorMessage } from "@/lib/api-error"
import { invalidateFinancialData } from "@/lib/invalidate"

const TYPE_LABELS: Record<TransactionType, string> = {
  RECEITA: "Receita",
  DESPESA: "Despesa",
  TRANSFERENCIA: "Transferência",
  RENDIMENTO: "Rendimento",
  AJUSTE: "Ajuste",
  PAGAMENTO_FATURA: "Pagamento fatura",
  PAGAMENTO_FINANCIAMENTO: "Pagamento financiamento",
  AMORTIZACAO: "Amortização",
}

const STATUS_VARIANT: Record<TransactionStatus, "success" | "warning" | "destructive"> = {
  CONFIRMADA: "success",
  PENDENTE: "warning",
  CANCELADA: "destructive",
}

// Lançamentos gerados pelo sistema que podem ser desfeitos (o backend desfaz a operação inteira:
// as duas pernas da transferência, o pagamento da fatura ou o da parcela).
const REVERSIBLE_TYPES: Partial<Record<TransactionType, string>> = {
  TRANSFERENCIA: "Desfazer esta transferência? As duas contas voltam ao saldo anterior.",
  PAGAMENTO_FATURA: "Desfazer este pagamento de fatura? O valor volta para a conta e a fatura fica em aberto de novo.",
  PAGAMENTO_FINANCIAMENTO: "Desfazer este pagamento de parcela? O valor volta para a conta e a parcela fica pendente de novo.",
}

export function TransactionsPage() {
  const [filters, setFilters] = useState<TransactionFilters>({ page: 1, page_size: 20 })
  const [showTransactionDialog, setShowTransactionDialog] = useState(false)
  const [showTransferDialog, setShowTransferDialog] = useState(false)
  // A busca só vira filtro 400 ms depois da última tecla — antes cada letra disparava uma
  // requisição (e um cold start na Vercel, se a função estivesse parada).
  const [searchText, setSearchText] = useState("")
  useEffect(() => {
    const timer = setTimeout(() => updateFilter("search", searchText.trim() || undefined), 400)
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchText])

  const { data: accounts } = useAccounts()
  const { data: categories } = useCategories()
  const flatCategories = flattenCategories(categories ?? [], { includeInactive: true })
  const queryClient = useQueryClient()
  const { notify } = useToast()

  const { data, isLoading } = useQuery({
    queryKey: ["transactions", filters],
    queryFn: () => transactionsApi.list(filters),
  })

  const cancelMutation = useMutation({
    mutationFn: transactionsApi.cancel,
    onSuccess: () => {
      invalidateFinancialData(queryClient)
      notify({ title: "Transação cancelada.", variant: "success" })
    },
    onError: (err: unknown) => notify({ title: getApiErrorMessage(err, "Não foi possível cancelar."), variant: "error" }),
  })

  const reverseMutation = useMutation({
    mutationFn: transactionsApi.reverse,
    onSuccess: () => {
      invalidateFinancialData(queryClient)
      notify({ title: "Lançamento desfeito.", variant: "success" })
    },
    onError: (err: unknown) => notify({ title: getApiErrorMessage(err, "Não foi possível desfazer."), variant: "error" }),
  })

  function updateFilter<K extends keyof TransactionFilters>(key: K, value: TransactionFilters[K]) {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }))
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / (filters.page_size ?? 20))) : 1

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Transações</h1>
          <p className="text-sm text-muted-foreground">{data?.total ?? 0} lançamento(s) encontrado(s)</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowTransferDialog(true)}>
            <ArrowLeftRight className="h-4 w-4" /> Transferir
          </Button>
          <Button onClick={() => setShowTransactionDialog(true)}>
            <Plus className="h-4 w-4" /> Nova movimentação
          </Button>
        </div>
      </div>

      <div className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar por descrição…"
            className="pl-9"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7">
          <Input type="date" onChange={(e) => updateFilter("date_from", e.target.value || undefined)} />
          <Input type="date" onChange={(e) => updateFilter("date_to", e.target.value || undefined)} />
          <Select onValueChange={(v) => updateFilter("type", v === "all" ? undefined : (v as TransactionType))}>
            <SelectTrigger>
              <SelectValue placeholder="Tipo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os tipos</SelectItem>
              {Object.entries(TYPE_LABELS).map(([value, label]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select onValueChange={(v) => updateFilter("status", v === "all" ? undefined : (v as TransactionStatus))}>
            <SelectTrigger>
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os status</SelectItem>
              <SelectItem value="CONFIRMADA">Confirmada</SelectItem>
              <SelectItem value="PENDENTE">Pendente</SelectItem>
              <SelectItem value="CANCELADA">Cancelada</SelectItem>
            </SelectContent>
          </Select>
          <Select onValueChange={(v) => updateFilter("account_id", v === "all" ? undefined : v)}>
            <SelectTrigger>
              <SelectValue placeholder="Conta" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas as contas</SelectItem>
              {accounts?.map((a) => (
                <SelectItem key={a.id} value={a.id}>
                  {a.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select onValueChange={(v) => updateFilter("category_id", v === "all" ? undefined : v)}>
            <SelectTrigger>
              <SelectValue placeholder="Categoria" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas as categorias</SelectItem>
              {flatCategories.map((c) => (
                <SelectItem key={c.id} value={c.id}>
                  {c.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            onValueChange={(v) =>
              updateFilter("payment_mode", v === "all" ? undefined : (v as "AVISTA" | "PARCELADO"))
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="À vista / Parcelado" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">À vista e parcelado</SelectItem>
              <SelectItem value="AVISTA">À vista</SelectItem>
              <SelectItem value="PARCELADO">Parcelado</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card">
        {isLoading ? (
          <div className="p-4">
            <Skeleton className="h-64 w-full" />
          </div>
        ) : !data || data.items.length === 0 ? (
          <p className="p-10 text-center text-sm text-muted-foreground">Nenhuma transação encontrada.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Data</TableHead>
                <TableHead>Descrição</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Valor</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((t) => (
                <TableRow key={t.id}>
                  <TableCell className="whitespace-nowrap text-muted-foreground">
                    {formatDate(t.competence_date)}
                  </TableCell>
                  <TableCell className="font-medium">{t.description}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{TYPE_LABELS[t.type]}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={STATUS_VARIANT[t.status]}>{t.status}</Badge>
                  </TableCell>
                  <TableCell
                    className={`font-mono-num text-right font-medium ${
                      t.type === "DESPESA" ? "text-destructive" : t.type === "RECEITA" || t.type === "RENDIMENTO" ? "text-success" : ""
                    }`}
                  >
                    {formatCurrency(t.amount)}
                  </TableCell>
                  <TableCell>
                    {["RECEITA", "DESPESA", "RENDIMENTO"].includes(t.type) &&
                      t.status !== "CANCELADA" &&
                      t.origin !== "CARTAO" && (
                      <button
                        title="Cancelar"
                        onClick={() => cancelMutation.mutate(t.id)}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                    {REVERSIBLE_TYPES[t.type] && t.status === "CONFIRMADA" && (
                      <button
                        title="Desfazer"
                        disabled={reverseMutation.isPending}
                        onClick={() =>
                          window.confirm(REVERSIBLE_TYPES[t.type]) &&
                          reverseMutation.mutate(t.id)
                        }
                        className="text-muted-foreground hover:text-destructive"
                      >
                        <Undo2 className="h-4 w-4" />
                      </button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {data && data.total > 0 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            Página {filters.page} de {totalPages}
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={(filters.page ?? 1) <= 1}
              onClick={() => setFilters((p) => ({ ...p, page: (p.page ?? 1) - 1 }))}
            >
              Anterior
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={(filters.page ?? 1) >= totalPages}
              onClick={() => setFilters((p) => ({ ...p, page: (p.page ?? 1) + 1 }))}
            >
              Próxima
            </Button>
          </div>
        </div>
      )}

      <TransactionFormDialog open={showTransactionDialog} onOpenChange={setShowTransactionDialog} />
      <TransferFormDialog open={showTransferDialog} onOpenChange={setShowTransferDialog} />
    </div>
  )
}
